from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple
import math
import json
from app.models.base import Laje
from app.models.value_objects import CondicaoContorno, CargaLinear

# Imports para cálculo em lote
from app.engines.analytic import AnalyticEngine
from app.controllers.slab_controller import SlabController

@dataclass
class LajePosicionada:
    """Wrapper que adiciona posição absoluta e metadados de vigas a uma Laje."""
    id: str # ex: "L1"
    laje: Laje
    x: float # Canto inferior esquerdo (Global)
    y: float # Canto inferior esquerdo (Global)
    
    # Mapeamento de bordas para nomes de vigas
    # Ex: {'esquerda': 'V1', 'direita': 'V2', 'topo': 'V3', 'fundo': 'V4'}
    vigas: Dict[str, str] = field(default_factory=dict)
    
    # Geometria das vigas de apoio (simplificado para string "15x40" para exportação)
    dim_vigas: str = "15x40"

    # [NOVO] Sobrescrita Manual de Vínculos
    # Ex: {'direita': 'livre', 'topo': 'engastado'}
    # Se uma borda estiver aqui, o algoritmo automático ignora a geometria para ela.
    vinculos_manuais: Dict[str, str] = field(default_factory=dict)
    
    @property
    def x_fim(self): return self.x + self.laje.lx
    @property
    def y_fim(self): return self.y + self.laje.ly

class GerenciadorPavimento:
    def __init__(self):
        self.lajes: List[LajePosicionada] = []
        self.paredes: List[CargaLinear] = []

    def limpar(self):
        self.lajes = []
        self.paredes = []

    def adicionar_laje(self, laje_pos: LajePosicionada):
        self.lajes.append(laje_pos)
        self.recalcular_vinculos()

    def adicionar_parede(self, parede: CargaLinear):
        self.paredes.append(parede)

    def definir_vinculo_manual(self, laje_id: str, borda: str, tipo: str):
        """
        Permite ao usuário forçar uma condição (ex: LIVRE para balanços).
        borda: 'esquerda', 'direita', 'topo', 'fundo'
        tipo: 'apoiado', 'engastado', 'livre'
        """
        for l in self.lajes:
            if l.id == laje_id:
                l.vinculos_manuais[borda] = tipo
                self.recalcular_vinculos() # Atualiza todo o sistema
                return

    def recalcular_vinculos(self):
        """
        Algoritmo Híbrido:
        1. Define padrão como APOIADO.
        2. Detecta continuidade geométrica (Automático).
        3. Aplica restrições manuais do usuário (Manual Overrides).
        """
        # 1. Resetar todas bordas para APOIADO
        for item in self.lajes:
            item.laje.bordas = {
                'esquerda': "apoiado", 'direita': "apoiado",
                'topo': "apoiado", 'fundo': "apoiado"
            }

        tol = 0.02 # Tolerância de 2cm

        # 2. Detecção Automática de Continuidade (Lajes Vizinhas)
        for i, l1 in enumerate(self.lajes):
            for j, l2 in enumerate(self.lajes):
                if i == j: continue

                # CASO 1: L2 está à DIREITA de L1
                if abs(l1.x_fim - l2.x) < tol:
                    y_start = max(l1.y, l2.y)
                    y_end = min(l1.y_fim, l2.y_fim)
                    if (y_end - y_start) > 0.10: 
                        l1.laje.bordas['direita'] = "engastado"
                        l2.laje.bordas['esquerda'] = "engastado"

                # CASO 2: L2 está ACIMA de L1
                if abs(l1.y_fim - l2.y) < tol:
                    x_start = max(l1.x, l2.x)
                    x_end = min(l1.x_fim, l2.x_fim)
                    if (x_end - x_start) > 0.10:
                        l1.laje.bordas['topo'] = "engastado"
                        l2.laje.bordas['fundo'] = "engastado"

        # 3. Aplicação de Vínculos Manuais (Soberania do Usuário)
        for item in self.lajes:
            for borda, tipo_manual in item.vinculos_manuais.items():
                if tipo_manual: # Se não for string vazia
                    item.laje.bordas[borda] = tipo_manual

    def _calcular_comprimento_intersecao(self, parede: CargaLinear, laje: LajePosicionada) -> float:
        """
        Calcula quanto da parede está dentro da laje usando algoritmo de Cohen-Sutherland ou Clipping simples.
        """
        # Limites da laje (Retângulo)
        xmin, xmax = laje.x, laje.x_fim
        ymin, ymax = laje.y, laje.y_fim
        
        p1 = (parede.x_inicio, parede.y_inicio)
        p2 = (parede.x_fim, parede.y_fim)

        # Verifica se a linha está totalmente fora (bounding box check)
        if max(p1[0], p2[0]) < xmin or min(p1[0], p2[0]) > xmax: return 0.0
        if max(p1[1], p2[1]) < ymin or min(p1[1], p2[1]) > ymax: return 0.0

        # Algoritmo de Clipping Liang-Barsky (Simplificado para segmento)
        t0, t1 = 0.0, 1.0
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        
        pq = [(-dx, p1[0] - xmin), (dx, xmax - p1[0]), 
              (-dy, p1[1] - ymin), (dy, ymax - p1[1])]
        
        for p, q in pq:
            if p == 0:
                if q < 0: return 0.0 # Paralela e fora
            else:
                t = q / p
                if p < 0:
                    if t > t1: return 0.0
                    if t > t0: t0 = t
                else:
                    if t < t0: return 0.0
                    if t < t1: t1 = t
        
        if t0 < t1:
            # Comprimento do segmento clipado
            clip_len = math.sqrt((dx*(t1-t0))**2 + (dy*(t1-t0))**2)
            return clip_len
            
        return 0.0

    def distribuir_cargas_paredes(self):
        """Distribui as cargas lineares como carga de área nas lajes afetadas."""
        # Resetar cargas de parede
        for item in self.lajes:
            item.laje.carregamento.g_paredes = 0.0

        for parede in self.paredes:
            for item in self.lajes:
                comp = self._calcular_comprimento_intersecao(parede, item)
                if comp > 0.01: # Se tiver mais de 1cm dentro da laje
                    peso_total = comp * parede.carga_kn_m # kN
                    area = item.laje.lx * item.laje.ly
                    q_eq = peso_total / area # kN/m²
                    
                    # Acumula na laje
                    item.laje.carregamento.g_paredes += q_eq

    def calcular_e_exportar_vigas(self, filepath: str):
        """
        Calcula todas as lajes, agrupa as reações e determina coordenadas das Vigas.
        Gera um JSON consolidado para o software de pórtico/vigas.
        """
        # 1. Preparação
        self.distribuir_cargas_paredes()
        engine = AnalyticEngine()
        
        # Estrutura temporária: vigas_data[nome] = { geometria, cargas_raw: [] }
        # cargas_raw guardará os dados brutos + coordenadas globais do trecho
        vigas_data = {}

        # 2. Coleta de Cargas e Geometria Global
        for item in self.lajes:
            controller = SlabController(item.laje, engine)
            result = controller.run_analysis()
            
            mapa = {
                'esquerda': {'nome': 'Esquerda', 'p1': (item.x, item.y), 'p2': (item.x, item.y_fim), 'k_m': 'mx_neg'},
                'direita':  {'nome': 'Direita',  'p1': (item.x_fim, item.y), 'p2': (item.x_fim, item.y_fim), 'k_m': 'mx_neg'},
                'topo':     {'nome': 'Topo',     'p1': (item.x, item.y_fim), 'p2': (item.x_fim, item.y_fim), 'k_m': 'my_neg'},
                'fundo':    {'nome': 'Fundo',    'p1': (item.x, item.y), 'p2': (item.x_fim, item.y), 'k_m': 'my_neg'}
            }

            for b_model, b_data in mapa.items():
                nome_viga = item.vigas.get(b_model, "").strip()
                # Se borda livre, não exporta carga para viga (pois não há viga)
                if not nome_viga or item.laje.bordas.get(b_model) == "livre": continue

                if nome_viga not in vigas_data:
                    vigas_data[nome_viga] = {
                        "id": nome_viga, 
                        "geometria_estimada": item.dim_vigas,
                        "cargas_raw": [], 
                        "coords_globais": [] # Lista de todos os pontos (p1, p2) encontrados
                    }
                
                # Guarda pontos para bounding box
                vigas_data[nome_viga]["coords_globais"].extend([b_data['p1'], b_data['p2']])
                
                # Dados básicos da carga
                comp_atuacao = item.laje.ly if b_model in ['esquerda', 'direita'] else item.laje.lx
                
                # Carga Vertical
                reac = result.reacoes_apoio.get(b_data['nome'], 0.0)
                if reac > 0:
                    vigas_data[nome_viga]["cargas_raw"].append({
                        "tipo": "vertical",
                        "valor": round(reac, 2),
                        "origem": item.id,
                        # Guarda as coordenadas GLOBAIS deste trecho de carga
                        "p_inicio": b_data['p1'],
                        "p_fim": b_data['p2']
                    })
                
                # Torção (Se engastado)
                if item.laje.bordas.get(b_model) == "engastado":
                    m_neg = result.momentos_kNm.get(b_data['k_m'], 0.0)
                    if m_neg == 0: 
                        q = result.carga_total_distribuida
                        l = (item.laje.lx**2) if b_model in ['esquerda', 'direita'] else (item.laje.ly**2)
                        m_neg = (q * l) / 12.0
                    
                    vigas_data[nome_viga]["cargas_raw"].append({
                        "tipo": "torsor",
                        "valor": round(m_neg, 2),
                        "origem": item.id,
                        "p_inicio": b_data['p1'],
                        "p_fim": b_data['p2']
                    })

        # 3. Processamento Final (Cálculo de Coordenadas Relativas)
        final_export = {}
        
        for nome, dados in vigas_data.items():
            coords = dados["coords_globais"]
            if not coords: continue

            # Determinar Bounding Box (Início e Fim da Viga Global)
            xs, ys = [p[0] for p in coords], [p[1] for p in coords]
            x_min, x_max = min(xs), max(xs)
            y_min, y_max = min(ys), max(ys)
            
            # Determinar Orientação
            # Se deltaX > deltaY -> Horizontal. Se não -> Vertical.
            eh_horizontal = (x_max - x_min) > (y_max - y_min)
            
            if eh_horizontal:
                # Viga Horizontal: Eixo principal é X
                # Normalizar Y (média para evitar erros de float)
                y_medio = sum(ys)/len(ys)
                p_start_global = (x_min, y_medio)
                comprimento_total = x_max - x_min
                eixo_principal = 0 # Index 0 é X
                coord_start_viga = x_min
            else:
                # Viga Vertical: Eixo principal é Y
                x_medio = sum(xs)/len(xs)
                p_start_global = (x_medio, y_min)
                comprimento_total = y_max - y_min
                eixo_principal = 1 # Index 1 é Y
                coord_start_viga = y_min

            # Processar as cargas para coordenadas relativas (0 a L)
            cargas_processadas = []
            for carga in dados["cargas_raw"]:
                # Pega a coordenada relevante (X ou Y) dos pontos globais da carga
                c_inicio_global = carga["p_inicio"][eixo_principal]
                c_fim_global = carga["p_fim"][eixo_principal]
                
                # Ordenar (pode vir invertido dependendo de como a laje foi desenhada)
                c_min = min(c_inicio_global, c_fim_global)
                c_max = max(c_inicio_global, c_fim_global)
                
                # Converter para relativo: Local = Global - OrigemViga
                pos_inicio = c_min - coord_start_viga
                pos_fim = c_max - coord_start_viga
                
                cargas_processadas.append({
                    "origem": carga["origem"],
                    "valor_kNm": carga["valor"],
                    "tipo": "Reacao Vertical" if carga["tipo"] == "vertical" else "Momento Torsor",
                    "posicao_na_viga": {
                        "inicio": round(pos_inicio, 3),
                        "fim": round(pos_fim, 3),
                        "comprimento": round(pos_fim - pos_inicio, 3)
                    }
                })

            final_export[nome] = {
                "id": nome,
                "geometria_estimada": dados["geometria_estimada"],
                "coordenadas_globais": {
                    "inicio": {"x": round(p_start_global[0], 3), "y": round(p_start_global[1], 3)},
                    "fim": {"x": round(x_max if eh_horizontal else x_medio, 3), 
                            "y": round(y_medio if eh_horizontal else y_max, 3)},
                    "comprimento_total": round(comprimento_total, 3)
                },
                "cargas_distribuidas": cargas_processadas
            }

        # 4. Escrita
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(final_export, f, indent=4, ensure_ascii=False)
            return True, f"Exportado com sucesso: {len(final_export)} vigas processadas."
        except Exception as e:
            return False, str(e)