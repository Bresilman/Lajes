"""
PyLaje - Configurações Globais e Parâmetros da NBR 6118:2023.
Este arquivo centraliza coeficientes de segurança, limites de serviço e caminhos de sistema.
"""

import os
from pathlib import Path

# ==============================================================================
# 1. CAMINHOS DE SISTEMA (PATH MANAGEMENT)
# ==============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
CATALOG_PATH = CONFIG_DIR / "engineering_catalogs.json"

# ==============================================================================
# 2. COEFICIENTES DE SEGURANÇA (ELU) - NBR 6118 Tabela 12.1 e 12.3
# ==============================================================================

# Coeficientes de ponderação das resistências (Combinações Normais)
GAMMA_C = 1.40  # Concreto
GAMMA_S = 1.15  # Aço

# Coeficientes de ponderação das ações (Combinações Normais)
GAMMA_G = 1.40  # Ações permanentes
GAMMA_Q = 1.40  # Ações variáveis

# ==============================================================================
# 3. PROPRIEDADES DOS MATERIAIS (VALORES PADRÃO)
# ==============================================================================

# Pesos específicos (kN/m³) - NBR 6120
PESO_ESPECIFICO_CONCRETO_ARMADO = 25.0
PESO_ESPECIFICO_CONCRETO_SIMPLES = 24.0

# Parâmetros para cálculo do Módulo de Elasticidade (Eci)
# Depende do tipo de agregado (Alfa_E): 1.2 granito, 1.0 quartzo, 0.9 calcário
ALFA_E = 1.0  

# ==============================================================================
# 4. LIMITES DE ESTADO LIMITE DE SERVIÇO (ELS) - NBR 6118 Tabela 13.3
# ==============================================================================

# Limites de Deformação (Flecha)
LIMITE_FLECHA_VISUAL = 1/250.0  # L/250 - Aceitabilidade sensorial
LIMITE_FLECHA_ESTRUTURAL = 1/500.0 # L/500 - Danos em alvenarias/acabamentos

# Coeficiente para cálculo de flecha diferida no tempo (NBR 6118 item 17.3.2.1.1)
# Valor de 'alfa' para t > 70 meses
ALFA_T_INFINITO = 2.0

# ==============================================================================
# 5. DURABILIDADE E PROTEÇÃO (CAA)
# ==============================================================================

# Mapeamento de Cobrimento Nominal (m) por Classe de Agressividade Ambiental
# NBR 6118 Tabela 7.2 (Lajes)
COBRIMENTO_POR_CAA = {
    1: 0.020, # CAA I
    2: 0.025, # CAA II
    3: 0.035, # CAA III (Mudança recente na norma para lajes)
    4: 0.045  # CAA IV
}

# ==============================================================================
# 6. CONFIGURAÇÕES DO OTIMIZADOR
# ==============================================================================

PASSO_INCREMENTO_H = 0.01  # Incremento de 1cm na busca pela espessura ideal
H_MIN_LAJE_MACICA = 0.07   # 7cm (Lajes de cobertura não em balanço)
H_MIN_LAJE_PISO = 0.08     # 8cm (Lajes de piso conforme NBR 6118 13.2.4.1)