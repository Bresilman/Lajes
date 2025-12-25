from abc import ABC, abstractmethod
from typing import Dict
from app.models.value_objects import Materiais, Carregamento, ClasseAgressividade, CondicaoContorno
from config import settings

class Laje(ABC):
    """
    Classe base para todas as lajes do sistema.
    Define o contrato e lida com propriedades comuns de norma.
    """
    def __init__(
        self,
        lx: float,
        ly: float,
        materiais: Materiais,
        caa: ClasseAgressividade,
        bordas: Dict[str, CondicaoContorno],
        carregamento: Carregamento
    ):
        self.lx = lx
        self.ly = ly
        self.materiais = materiais
        self.caa = caa
        self.bordas = bordas
        self.carregamento = carregamento
        
        # Atributos protegidos que serão definidos pelas subclasses
        self._h: float = 0.0  # Espessura total (m)
        self._d: float = 0.0  # Altura útil (m)

    @property
    def h(self) -> float:
        return self._h

    @property
    def d(self) -> float:
        return self._d

    @property
    def cobrimento(self) -> float:
        """Retorna o cobrimento nominal (m) baseado na CAA via settings."""
        return settings.COBRIMENTO_POR_CAA.get(self.caa.value, 0.025)

    @abstractmethod
    def get_peso_proprio(self) -> float:
        """kN/m²"""
        pass

    @abstractmethod
    def get_inercia_flexao(self) -> float:
        """Inércia equivalente por metro (m4/m)"""
        pass

    @abstractmethod
    def calcular_altura_util(self):
        """Define o valor de d baseado em h e armaduras."""
        pass