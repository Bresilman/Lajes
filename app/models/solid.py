from app.models.base import Laje
from config import settings

class LajeMacica(Laje):
    """Implementação para lajes maciças de concreto armado."""
    
    def __init__(self, h: float, **kwargs):
        super().__init__(**kwargs)
        self._h = h
        self.calcular_altura_util()

    def calcular_altura_util(self):
        # Estimativa: d = h - cobrimento - phi/2 (considerando phi=10mm)
        self._d = self.h - self.cobrimento - 0.005

    def get_peso_proprio(self) -> float:
        return self.h * settings.PESO_ESPECIFICO_CONCRETO_ARMADO

    def get_inercia_flexao(self) -> float:
        # b*h³/12 (para b=1m)
        return (1.0 * (self.h ** 3)) / 12