import math
from typing import List, Dict, Optional, Tuple

class SteelDetailer:
    """
    Serviço responsável por converter Área de Aço Teórica (cm²/m)
    em bitolas comerciais e espaçamentos reais (Ø c/ s).
    """
    
    # Bitolas padrão (diâmetro mm, área cm²)
    # Em um sistema real, isso viria do engineering_catalogs.json
    BARS = [
        {"phi": 5.0, "area": 0.20, "peso": 0.154},
        {"phi": 6.3, "area": 0.315, "peso": 0.245},
        {"phi": 8.0, "area": 0.50, "peso": 0.395},
        {"phi": 10.0, "area": 0.785, "peso": 0.617},
        {"phi": 12.5, "area": 1.23, "peso": 0.963}
    ]

    @staticmethod
    def encontrar_melhor_armadura(as_req: float, h_laje_m: float) -> Dict[str, str]:
        """
        Recebe As necessário (cm²/m) e retorna a melhor configuração.
        Ex: {'descricao': 'Ø6.3 c/15', 'as_real': 0.35, 'peso_kg_m2': 2.5}
        """
        if as_req <= 0:
            return {"texto": "Dispensa", "peso_total": 0.0}

        melhor_solucao = None
        menor_sobra = 999.0

        # Regras de espaçamento NBR 6118
        esp_max = min(20.0, 2 * (h_laje_m * 100)) # cm
        esp_min = 7.0 # cm (para facilitar concretagem)
        
        # Espaçamentos comerciais (passo de 2.5cm)
        passos = [7.5, 10.0, 12.5, 15.0, 17.5, 20.0]

        for bar in SteelDetailer.BARS:
            for s in passos:
                if s > esp_max: continue
                
                # As fornecido pela configuração (cm²/m) = (100 / s) * area_barra
                as_real = (100.0 / s) * bar['area']
                
                if as_real >= as_req:
                    sobra = as_real - as_req
                    
                    # Critério de escolha: Menor sobra (economia) com preferência por bitolas menores em lajes
                    if sobra < menor_sobra:
                        menor_sobra = sobra
                        peso_por_m2 = (100.0 / s) * bar['peso'] # 1m largura * (100/s barras) * peso linear
                        
                        melhor_solucao = {
                            "texto": f"Ø{bar['phi']} c/{s:g}", # :g remove zeros decimais inúteis
                            "as_real": round(as_real, 2),
                            "peso_kg_m2": peso_por_m2,
                            "bitola": bar['phi'],
                            "espacamento": s
                        }

        if not melhor_solucao:
            return {"texto": "Erro: Muito Armado", "peso_total": 0.0}
            
        return melhor_solucao