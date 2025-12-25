from abc import ABC, abstractmethod
from typing import Dict, Any
from app.models.base import Laje

class ICalculationEngine(ABC):
    """
    Interface abstrata que define o que qualquer motor de cálculo deve realizar.
    """

    @abstractmethod
    def calcular_esforcos_elu(self, laje: Laje) -> Dict[str, float]:
        """Calcula momentos fletores (Md)."""
        pass

    @abstractmethod
    def verificar_cisalhamento(self, laje: Laje, as_flexao: Dict[str, float]) -> Dict[str, Any]:
        """
        Verifica a resistência ao esforço cortante (VRd1 vs VSd).
        Necessita da armadura longitudinal (as_flexao) para cálculo do efeito pino (rho).
        """
        pass

    @abstractmethod
    def dimensionar_armaduras(self, laje: Laje, esforcos: Dict[str, float]) -> Dict[str, Any]:
        """Calcula a área de aço necessária (As)."""
        pass

    @abstractmethod
    def verificar_els(self, laje: Laje) -> Dict[str, Any]:
        """Verificações de serviço (Flecha)."""
        pass