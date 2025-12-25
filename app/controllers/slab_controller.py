# app/controllers/slab_controller.py
from typing import Dict, Any, Optional
from app.models.base import Laje
from app.models.value_objects import AnalysisResult
from app.engines.interfaces import ICalculationEngine
from app.services.steel_detailer import SteelDetailer
from config import settings

class SlabController:
    def __init__(self, model: Laje, engine: ICalculationEngine):
        self.model = model
        self.engine = engine
        self.last_result: Optional[AnalysisResult] = None

    def run_analysis(self) -> AnalysisResult:
        # 1. Cálculos de Norma
        esforcos = self.engine.calcular_esforcos_elu(self.model)
        armaduras = self.engine.dimensionar_armaduras(self.model, esforcos)
        verif_cortante = self.engine.verificar_cisalhamento(self.model, armaduras)
        verif_els = self.engine.verificar_els(self.model)
        
        # 2. NOVA: Verificação de Fissuração (Wk)
        verif_wk = self.engine.verificar_fissuracao(self.model, esforcos, armaduras)

        # 3. Reações de Apoio para Vigas
        reacoes = {
            "Esquerda": esforcos.get('reacao_viga_y', 0.0),
            "Direita":  esforcos.get('reacao_viga_y', 0.0),
            "Topo":     esforcos.get('reacao_viga_x', 0.0),
            "Fundo":    esforcos.get('reacao_viga_x', 0.0)
        }

        # 4. Detalhamento e Quantitativos
        detalhe_map = {}
        peso_total_aco = 0.0
        area_laje = self.model.lx * self.model.ly
        pp = self.model.get_peso_proprio()

        for pos in ['mx', 'my', 'mx_neg', 'my_neg']:
            as_req = armaduras.get(pos, 0.0)
            if isinstance(as_req, (int, float)) and as_req > 0:
                solucao = SteelDetailer.encontrar_melhor_armadura(as_req, self.model.h)
                detalhe_map[pos] = solucao.get('texto', "Mínima")
                fator_area = 0.30 if "neg" in pos else 1.0
                peso_total_aco += (solucao.get('peso_kg_m2', 0) * area_laje * fator_area)
            else:
                detalhe_map[pos] = "Mínima"

        vol_concreto = (pp / 25.0) * area_laje
        taxa_aco = (peso_total_aco * 1.15) / area_laje if area_laje > 0 else 0
        
        flecha_total = verif_els.get("flecha_total_mm", 0.0)
        contraflecha = round(flecha_total / 2.0, 0) if flecha_total > 5.0 else 0.0

        q_tot = self.model.carregamento.permanente_total(pp) + self.model.carregamento.q_acidental

        # 5. Consolidação (Sincronizado com DTO)
        self.last_result = AnalysisResult(
            tipo_laje=type(self.model).__name__,
            lx=self.model.lx, ly=self.model.ly,
            h_cm=round(self.model.h * 100, 2),
            d_cm=round(self.model.d * 100, 2),
            peso_proprio=round(pp, 2),
            carga_total_distribuida=round(q_tot, 2),
            momentos_kNm=esforcos,
            as_teorico=armaduras,
            cortante=verif_cortante,
            detalhamento=detalhe_map,
            reacoes_apoio=reacoes,
            volume_concreto=round(vol_concreto, 2),
            peso_aco_estimado=round(peso_total_aco * 1.15, 1),
            taxa_aco_m2=round(taxa_aco, 2),
            consumo_concreto_m2=round(vol_concreto / area_laje, 3),
            cobrimento_mm=round(self.model.cobrimento * 1000, 1),
            flecha_total_mm=round(flecha_total, 2),
            flecha_limite_mm=round(verif_els.get("limite_norma_mm", 0.0), 2),
            contraflecha_mm=contraflecha,
            wk_max_mm=verif_wk['wk_max_mm'],
            status_servico=verif_els.get("status", "ERRO"),
            status_geral="APROVADO" if (verif_els['status'] == "OK" and verif_cortante['status'] == "OK" and verif_wk['status'] == "OK") else "REPROVADO"
        )
        return self.last_result

    def optimize_thickness(self) -> Optional[float]:
        current_h = settings.H_MIN_LAJE_PISO
        while current_h <= 0.35:
            self.model._h = current_h
            self.model.calcular_altura_util()
            res = self.run_analysis()
            if res.status_geral == "APROVADO":
                return current_h
            current_h += settings.PASSO_INCREMENTO_H
        return None