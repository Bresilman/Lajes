from typing import Dict, Any
from app.models.base import Laje
from config import settings

class LajeTrelicada(Laje):
    """Implementação para lajes nervuradas treliçadas unidirecionais."""
    
    def __init__(
        self, 
        h_capa: float, 
        largura_sapata: float, 
        dados_enchimento: Dict[str, Any], 
        **kwargs
    ):
        super().__init__(**kwargs)
        self.h_capa = h_capa
        self.largura_sapata = largura_sapata
        self.enchimento = dados_enchimento
        
        # Geometria
        self.h_enchimento = self.enchimento['altura_h_cm'] / 100.0
        self._h = self.h_enchimento + self.h_capa
        
        # Intereixo
        self.intereixo = (self.enchimento['largura_b_cm'] / 100.0) + self.largura_sapata
        self.calcular_altura_util()

    def calcular_altura_util(self):
        # Para treliçadas, d é medido até o CG da armadura inferior da treliça
        self._d = self.h - self.cobrimento - 0.005

    def get_peso_proprio(self) -> float:
        # Cálculo volumétrico por metro quadrado
        vol_capa = 1.0 * 1.0 * self.h_capa
        
        num_nervuras = 1.0 / self.intereixo
        vol_nervuras = (self.largura_sapata * self.h_enchimento) * num_nervuras
        
        peso_concreto = (vol_capa + vol_nervuras) * settings.PESO_ESPECIFICO_CONCRETO_ARMADO
        
        # Peso do enchimento
        comp_bloco = self.enchimento.get('comprimento_cm', 30.0) / 100.0
        qtd_blocos = (1.0 / comp_bloco) * num_nervuras
        peso_enchimento = (qtd_blocos * self.enchimento['peso_unitario_kg']) * 0.00981 # kg to kN
        
        return peso_concreto + peso_enchimento

    def get_inercia_flexao(self) -> float:
        # Cálculo de inércia de seção T
        bw = self.largura_sapata
        bf = self.intereixo
        hf = self.h_capa
        h = self.h
        
        # Centroide y_cg (base)
        a1, y1 = bf * hf, h - (hf/2)
        a2, y2 = bw * (h - hf), (h - hf) / 2
        y_cg = (a1*y1 + a2*y2) / (a1 + a2)
        
        # Teorema dos eixos paralelos
        i1 = (bf * hf**3)/12 + a1 * (y1 - y_cg)**2
        i2 = (bw * (h-hf)**3)/12 + a2 * (y2 - y_cg)**2
        
        # Inércia por metro
        return (i1 + i2) / self.intereixo