# MEMORIAL DE CÁLCULO ESTRUTURAL: PROJETO RESIDENCIAL
**Data de Emissão:** 06/01/2026

## 1. INTRODUÇÃO E NORMAS
Este documento apresenta o dimensionamento das lajes do projeto, seguindo rigorosamente os critérios da **NBR 6118:2023 (Projeto de estruturas de concreto)** e as cargas estabelecidas pela **NBR 6120:2019 (Ações para o cálculo de estruturas de edificações)**.

---

## 2. ANÁLISE DA LAJE: LajeMacica (ID: 4.0x5.0)

### 2.1 Dados de Entrada
* **Geometria:** 4.00 m x 5.00 m
* **Espessura (h):** 13.0 cm (Altura útil d = 10.0 cm)
* **Cobrimento Nominal:** 25.0 mm

### 2.2 Carregamento e Combinações
| Descrição | Valor (kN/m²) |
| :--- | :--- |
| Peso Próprio | 3.25 |
| Carga Total (Calculada $p_d$) | **7.00** |

### 2.3 Análise Estrutural (Momentos de Cálculo)
Utilizado método de Marcus/Bares para $\lambda = 1.25$.
* $M_{dx}$: 8.60 kNm/m
* $M_{dy}$: 4.63 kNm/m

### 2.4 Dimensionamento (ELU)
* **Armadura Principal (X):** Ø6.3 c/15 (Teórico: 2.03 cm²/m)
* **Armadura Secundária (Y):** Ø5.0 c/10 (Teórico: 1.95 cm²/m)
* **Cisalhamento:** Ratio 0.377 - Status: OK

### 2.5 Verificações de Serviço (ELS)
* **Flecha Total:** 12.71 mm (Limite $L/250$: 16.00 mm)
* **Contraflecha Sugerida:** 6.0 mm
* **Abertura de Fissuras ($w_k$):** 0.172 mm - Status: OK

### 2.6 Quantitativos Estritos
* Volume de Concreto: 2.60 m³
* Peso de Aço Estimado: 73.00 kg
* Taxa de Aço: 3.65 kg/m²

---

**Responsável Técnico:** Software PyLaje - NBR 6118:2023