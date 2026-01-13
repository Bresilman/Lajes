from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Any
from config import settings

class ClasseAgressividade(Enum):
    I = 1
    II = 2
    III = 3
    IV = 4

class CondicaoContorno(Enum):
    LIVRE = "Livre"
    APOIADO = "Apoiado"
    ENGASTADO = "Engastado"

@dataclass
class CargaLinear:
    """Representa uma parede ou carga linear sobre a laje."""
    id: str
    x_inicio: float
    y_inicio: float
    x_fim: float
    y_fim: float
    carga_kn_m: float # Carga por metro linear

    @property
    def comprimento(self) -> float:
        return ((self.x_fim - self.x_inicio)**2 + (self.y_fim - self.y_inicio)**2)**0.5

@dataclass
class Materiais:
    fck: float
    fyk: float
    Ecs: float
    gamma_c: float = settings.GAMMA_C
    gamma_s: float = settings.GAMMA_S

@dataclass
class Carregamento:
    g_revestimento: float
    q_acidental: float
    g_paredes: float = 0.0 # Carga distribuída equivalente de paredes
    
    def permanente_total(self, peso_proprio: float) -> float:
        """Soma: Revestimento + Paredes Distribuídas + Peso Próprio"""
        return self.g_revestimento + self.g_paredes + peso_proprio

@dataclass
class AnalysisResult:
    tipo_laje: str
    lx: float
    ly: float
    h_cm: float
    d_cm: float
    peso_proprio: float
    carga_total_distribuida: float
    momentos_kNm: Dict[str, float]
    as_teorico: Dict[str, float]
    cortante: Dict[str, Any]
    detalhamento: Dict[str, str]
    reacoes_apoio: Dict[str, float]
    volume_concreto: float
    peso_aco_estimado: float
    taxa_aco_m2: float
    consumo_concreto_m2: float
    cobrimento_mm: float
    flecha_total_mm: float
    flecha_limite_mm: float
    contraflecha_mm: float
    wk_max_mm: float
    status_servico: str
    status_geral: str