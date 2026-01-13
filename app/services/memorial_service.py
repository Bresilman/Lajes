import os
from datetime import datetime
from typing import List
from app.models.value_objects import AnalysisResult

class MemorialService:
    """
    Serviço responsável por transformar os resultados de análise em um 
    documento textual técnico (Memorial de Cálculo) seguindo a NBR 6118.
    """

    @staticmethod
    def gerar_markdown(resultados: List[AnalysisResult], titulo_projeto: str = "Projeto Residencial") -> str:
        """
        Gera um memorial completo em formato Markdown contendo uma ou mais lajes.
        """
        data_atual = datetime.now().strftime("%d/%m/%Y")
        
        md = [
            f"# MEMORIAL DE CÁLCULO ESTRUTURAL: {titulo_projeto.upper()}",
            f"**Data de Emissão:** {data_atual}",
            "\n## 1. INTRODUÇÃO E NORMAS",
            "Este documento apresenta o dimensionamento das lajes do projeto, seguindo rigorosamente os critérios da **NBR 6118:2023 (Projeto de estruturas de concreto)** e as cargas estabelecidas pela **NBR 6120:2019 (Ações para o cálculo de estruturas de edificações)**.",
            "\n---"
        ]

        for res in resultados:
            md.append(f"\n## 2. ANÁLISE DA LAJE: {res.tipo_laje} (ID: {res.lx}x{res.ly})")
            
            # 2.1 Dados de Entrada
            md.append("\n### 2.1 Dados de Entrada")
            md.append(f"* **Geometria:** {res.lx:.2f} m x {res.ly:.2f} m")
            md.append(f"* **Espessura (h):** {res.h_cm:.1f} cm (Altura útil d = {res.d_cm:.1f} cm)")
            md.append(f"* **Cobrimento Nominal:** {res.cobrimento_mm:.1f} mm")
            
            # 2.2 Carregamento
            md.append("\n### 2.2 Carregamento e Combinações")
            md.append("| Descrição | Valor (kN/m²) |")
            md.append("| :--- | :--- |")
            md.append(f"| Peso Próprio | {res.peso_proprio:.2f} |")
            md.append(f"| Carga Total (Calculada $p_d$) | **{res.carga_total_distribuida:.2f}** |")

            # 2.3 Esforços
            md.append("\n### 2.3 Análise Estrutural (Momentos de Cálculo)")
            md.append(f"Utilizado método de Marcus/Bares para $\\lambda = {res.ly/res.lx:.2f}$.")
            md.append(f"* $M_{{dx}}$: {res.momentos_kNm.get('mx', 0):.2f} kNm/m")
            md.append(f"* $M_{{dy}}$: {res.momentos_kNm.get('my', 0):.2f} kNm/m")
            
            m_neg_x = res.momentos_kNm.get('mx_neg', 0)
            m_neg_y = res.momentos_kNm.get('my_neg', 0)
            if m_neg_x > 0 or m_neg_y > 0:
                md.append(f"* $M_{{neg}}$ Máximo: {max(m_neg_x, m_neg_y):.2f} kNm/m")

            # 2.4 Dimensionamento ELU
            md.append("\n### 2.4 Dimensionamento (ELU)")
            md.append(f"* **Armadura Principal (X):** {res.detalhamento.get('mx', 'Mínima')} (Teórico: {res.as_teorico.get('mx', 0):.2f} cm²/m)")
            md.append(f"* **Armadura Secundária (Y):** {res.detalhamento.get('my', 'Mínima')} (Teórico: {res.as_teorico.get('my', 0):.2f} cm²/m)")
            md.append(f"* **Cisalhamento:** Ratio {res.cortante.get('ratio', 0)} - Status: {res.cortante.get('status', 'OK')}")

            # 2.5 ELS
            md.append("\n### 2.5 Verificações de Serviço (ELS)")
            md.append(f"* **Flecha Total:** {res.flecha_total_mm:.2f} mm (Limite $L/250$: {res.flecha_limite_mm:.2f} mm)")
            if res.contraflecha_mm > 0:
                md.append(f"* **Contraflecha Sugerida:** {res.contraflecha_mm:.1f} mm")
            md.append(f"* **Abertura de Fissuras ($w_k$):** {res.wk_max_mm:.3f} mm - Status: {res.status_servico}")

            # 2.6 Quantitativos
            md.append("\n### 2.6 Quantitativos Estritos")
            md.append(f"* Volume de Concreto: {res.volume_concreto:.2f} m³")
            md.append(f"* Peso de Aço Estimado: {res.peso_aco_estimado:.2f} kg")
            md.append(f"* Taxa de Aço: {res.taxa_aco_m2:.2f} kg/m²")
            md.append("\n---")

        md.append("\n**Responsável Técnico:** Software PyLaje - NBR 6118:2023")
        
        return "\n".join(md)

    @staticmethod
    def salvar_arquivo(conteudo: str, caminho: str):
        """Salva o conteúdo em um arquivo .md"""
        try:
            with open(caminho, 'w', encoding='utf-8') as f:
                f.write(conteudo)
            return True
        except Exception as e:
            print(f"Erro ao salvar memorial: {e}")
            return False