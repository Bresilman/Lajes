# app/services/report_formatter.py
import json
import dataclasses
from app.controllers.slab_controller import AnalysisResult

class ReportFormatter:
    
    @staticmethod
    def format_as_text(res: AnalysisResult) -> str:
        lines = [
            f"=== RELATÓRIO EXECUTIVO: {res.tipo_laje} ===",
            f"Dimensões: {res.lx} x {res.ly} m (Área: {res.lx*res.ly:.1f} m²)",
            f"Espessura: h = {res.h_cm} cm (d = {res.d_cm} cm)",
            f"Carga Total: {res.carga_total_distribuida} kN/m² (PP: {res.peso_proprio})",
            f"Cobrimento: {res.cobrimento_mm} mm (Normativo NBR)",
            "-"*45,
            "1. DETALHAMENTO DE ARMADURAS:"
        ]
        
        labels = {'mx': 'Positiva Lx (Principal)', 'my': 'Positiva Ly (Secundária)', 
                  'mx_neg': 'Negativa (Apoios)', 'my_neg': 'Negativa (Distrib.)'}
        
        for key, label in labels.items():
            as_req = res.as_teorico.get(key, 0.0)
            detalhe = res.detalhamento.get(key, '-')
            if isinstance(as_req, (int, float)) and as_req > 0:
                lines.append(f"  {label:<25} : {detalhe:<15} ({as_req} cm²/m)")
            
        lines.append("-" * 45)
        lines.append("2. REAÇÕES NOS APOIOS (Cargas p/ Vigas - kN/m):")
        for bordo, carga in res.reacoes_apoio.items():
            lines.append(f"  {bordo:<25} : {carga:.2f} kN/m")

        lines.append("-" * 45)
        lines.append("3. QUANTITATIVOS E EFICIÊNCIA:")
        lines.append(f"  Volume Concreto   : {res.volume_concreto} m³ ({res.consumo_concreto_m2} m³/m²)")
        lines.append(f"  Peso Aço Total    : {res.peso_aco_estimado} kg ({res.taxa_aco_m2} kg/m²)")

        lines.append("-" * 45)
        lines.append("4. VERIFICAÇÕES DE SERVIÇO (ELS):")
        lines.append(f"  Flecha Total      : {res.flecha_total_mm} mm (Limite: {res.flecha_limite_mm} mm)")
        if res.contraflecha_mm > 0:
            lines.append(f"  CONTRAFLECHA SUG. : {res.contraflecha_mm} mm")
        
        lines.append(f"  Abertura Fissuras : {res.wk_max_mm} mm (Limite NBR: 0.2 a 0.4 mm)")
        lines.append(f"  STATUS SERVIÇO    : {res.status_servico}")
        
        lines.append("-" * 45)
        lines.append("5. SEGURANÇA E CONCLUSÃO (ELU):")
        lines.append(f"  Cisalhamento Ratio: {res.cortante.get('ratio',0)} ({res.cortante.get('status','-')})")
        lines.append(f"  STATUS GERAL      : {res.status_geral}")
        lines.append("="*45)
        
        return "\n".join(lines)

    @staticmethod
    def save_json(res: AnalysisResult, filepath: str):
        data = dataclasses.asdict(res)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)