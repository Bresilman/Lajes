from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from app.models.base import Laje
from app.engines.interfaces import ICalculationEngine
from app.services.steel_detailer import SteelDetailer
from config import settings

@dataclass
class AnalysisResult:
    tipo_laje: str
    lx: float
    ly: float
    h_cm: float
    d_cm: float
    # Cargas e Materiais
    peso_proprio: float
    carga_total_distribuida: float # kN/m² (total)
    
    # Engenharia
    momentos_kNm: Dict[str, float]
    as_teorico: Dict[str, float]
    cortante: Dict[str, Any]
    
    # Detalhamento e Quantitativo (Novos)
    detalhamento: Dict[str, str] # Ex: 'mx': 'Ø6.3 c/15'
    reacoes_apoio: Dict[str, float] # kN/m linear em cada borda
    volume_concreto: float # m³
    peso_aco_estimado: float # kg
    
    # Serviço
    flecha_total_mm: float
    flecha_limite_mm: float
    status_servico: str
    status_geral: str

class SlabController:
    def __init__(self, model: Laje, engine: ICalculationEngine):
        self.model = model
        self.engine = engine
        self.last_result: Optional[AnalysisResult] = None

    def run_analysis(self) -> AnalysisResult:
        # 1. Engenharia Pura
        esforcos = self.engine.calcular_esforcos_elu(self.model)
        armaduras = self.engine.dimensionar_armaduras(self.model, esforcos)
        verif_cortante = self.engine.verificar_cisalhamento(self.model, armaduras)
        verif_els = self.engine.verificar_els(self.model)

        # 2. Pós-Processamento: Reações de Apoio (Load Takedown)
        # Simplificação: V_sd é a reação por metro linear aproximada na direção do vão
        # Esquerda/Direita recebem carga do vão Lx (Vx)
        # Topo/Fundo recebem carga do vão Ly (Vy)
        reacoes = {
            "Esquerda": esforcos.get('v_sd_x', 0.0),
            "Direita": esforcos.get('v_sd_x', 0.0),
            "Topo (Sup)": esforcos.get('v_sd_y', 0.0),
            "Fundo (Inf)": esforcos.get('v_sd_y', 0.0)
        }

        # 3. Detalhamento e Quantitativos
        detalhe_map = {}
        peso_total_aco = 0.0
        area_laje = self.model.lx * self.model.ly

        for pos in ['mx', 'my', 'mx_neg', 'my_neg']: # Iterar chaves principais
            as_req = armaduras.get(pos, 0.0)
            if isinstance(as_req, str): # Erro de ductilidade
                detalhe_map[pos] = "Erro"
                continue
                
            solucao = SteelDetailer.encontrar_melhor_armadura(as_req, self.model.h)
            detalhe_map[pos] = solucao['texto']
            
            # Estimativa de peso: peso/m² * área da laje
            # Nota: Armadura negativa não cobre a laje toda (aprox 1/4 do vão), 
            # mas simplificaremos assumindo cobrimento total por segurança no orçamento preliminar
            fator_comprimento = 0.30 if "neg" in pos else 1.0
            peso_total_aco += (solucao.get('peso_kg_m2', 0) * area_laje * fator_comprimento)

        # Volume de Concreto
        # Maciça: lx * ly * h. Treliçada: lx * ly * h_equivalente (peso_proprio / 25)
        # Usaremos peso próprio para estimar volume equivalente de concreto
        vol_concreto = (self.model.get_peso_proprio() / 25.0) * area_laje

        # Avaliação Global
        status_geral = "APROVADO"
        if verif_els['status'] != "OK" or verif_cortante['status'] != "OK":
            status_geral = "REPROVADO"
        
        # Carga Total (Perm + Acid + PP) para referência
        q_tot = self.model.carregamento.permanente_total(self.model.get_peso_proprio()) + self.model.carregamento.q_acidental

        self.last_result = AnalysisResult(
            tipo_laje=type(self.model).__name__,
            lx=self.model.lx, ly=self.model.ly,
            h_cm=round(self.model.h * 100, 2),
            d_cm=round(self.model.d * 100, 2),
            peso_proprio=round(self.model.get_peso_proprio(), 2),
            carga_total_distribuida=round(q_tot, 2),
            momentos_kNm=esforcos,
            as_teorico=armaduras,
            cortante=verif_cortante,
            detalhamento=detalhe_map,
            reacoes_apoio=reacoes,
            volume_concreto=round(vol_concreto, 2),
            peso_aco_estimado=round(peso_total_aco * 1.1, 1), # +10% de perdas/transpasses
            flecha_total_mm=verif_els.get("flecha_total_mm", 0.0),
            flecha_limite_mm=verif_els.get("limite_norma_mm", 0.0),
            status_servico=verif_els.get("status", "ERRO"),
            status_geral=status_geral
        )
        
        return self.last_result

    def optimize_thickness(self) -> Optional[float]:
        current_h = settings.H_MIN_LAJE_PISO
        while current_h <= 0.30:
            self.model._h = current_h
            self.model.calcular_altura_util()
            res = self.run_analysis()
            if res.status_geral == "APROVADO":
                return current_h
            current_h += settings.PASSO_INCREMENTO_H
        return None