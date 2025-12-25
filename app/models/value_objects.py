# app/models/value_objects.py
from enum import Enum
from dataclasses import dataclass
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
class Materiais:
    fck: float
    fyk: float
    Ecs: float # Módulo em GPa
    gamma_c: float = settings.GAMMA_C
    gamma_s: float = settings.GAMMA_S

@dataclass
class Carregamento:
    g_revestimento: float
    q_acidental: float
    
    def permanente_total(self, peso_proprio: float) -> float:
        """Calcula a carga permanente total somando revestimento e peso próprio."""
        return self.g_revestimento + peso_proprio

@dataclass
class AnalysisResult:
    """Objeto de Transferência de Dados (DTO) para a UI."""
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