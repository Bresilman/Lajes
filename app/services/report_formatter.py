from app.controllers.slab_controller import AnalysisResult

class ReportFormatter:
    """Transforma dados brutos em strings formatadas para a UI ou PDF."""
    
    @staticmethod
    def format_as_text(res: AnalysisResult) -> str:
        lines = [
            f"=== RELATÓRIO EXECUTIVO: {res.tipo_laje} ===",
            f"Dimensões: {res.lx} x {res.ly} m (Área: {res.lx*res.ly:.1f} m²)",
            f"Espessura: h = {res.h_cm} cm (d = {res.d_cm} cm)",
            f"Carga Total: {res.carga_total_distribuida} kN/m² (PP: {res.peso_proprio})",
            "-"*45,
            "1. DETALHAMENTO DE ARMADURAS (Sugestão):"
        ]
        
        labels = {
            'mx': 'Positiva X (Vão Menor)', 
            'my': 'Positiva Y (Vão Maior)', 
            'mx_neg': 'Negativa (Bordas)', 
            'my_neg': 'Negativa (Secundária)'
        }

        for key, label in labels.items():
            as_val = res.as_teorico.get(key, 0.0)
            detalhe = res.detalhamento.get(key, '-')
            if isinstance(as_val, (int, float)) and as_val > 0:
                lines.append(f"  {label:<25} : {detalhe:<15} (As req: {as_val} cm²/m)")
            
        lines.append("-" * 45)
        lines.append("2. REAÇÕES NOS APOIOS (Cargas p/ Vigas):")
        lines.append("   (Cargas lineares distribuídas kN/m)")
        for bordo, carga in res.reacoes_apoio.items():
            lines.append(f"  {bordo:<15} : {carga:.2f} kN/m")

        lines.append("-" * 45)
        lines.append("3. QUANTITATIVOS ESTIMADOS:")
        lines.append(f"  Volume de Concreto : {res.volume_concreto} m³")
        lines.append(f"  Peso de Aço (aprox): {res.peso_aco_estimado} kg")

        lines.append("-" * 45)
        lines.append(f"4. VERIFICAÇÕES DE NORMA (ELS/ELU):")
        lines.append(f"  Flecha: {res.flecha_total_mm}mm (Limite: {res.flecha_limite_mm}mm) -> {res.status_servico}")
        lines.append(f"  Cisalhamento: Ratio {res.cortante.get('ratio',0)} -> {res.cortante.get('status','-')}")
        lines.append(f"  STATUS GERAL: {res.status_geral}")
        lines.append("="*45)
        
        return "\n".join(lines)