import json
from typing import Dict, Tuple, Any, List
from pathlib import Path

class TableSolver:
    """
    Implementação dos coeficientes de Marcus.
    Agora suporta coeficientes de cisalhamento (mu_x, mu_y).
    """

    _cached_data: Dict[str, Any] = {}

    @classmethod
    def _load_data(cls):
        if not cls._cached_data:
            path = Path(__file__).parent.parent.parent / "config" / "coefficients_table.json"
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    cls._cached_data = json.load(f)
            except Exception as e:
                print(f"Erro JSON: {e}")
                cls._cached_data = {"casos_marcus": {}}

    @staticmethod
    def get_coefficients(caso: int, lam: float) -> Dict[str, float]:
        """
        Retorna dicionário com todos os coeficientes interpolados:
        {'alpha_x', 'alpha_y', 'mu_x', 'mu_y'}
        """
        TableSolver._load_data()
        
        casos = TableSolver._cached_data.get("casos_marcus", {})
        dados_caso = casos.get(str(caso), {}).get("dados", [])
        
        # Fallback
        if not dados_caso:
            return {"alpha_x": 10.0, "alpha_y": 10.0 * lam**2, "mu_x": 0.5, "mu_y": 0.5}

        # Ordenar
        dados_sorted = sorted(dados_caso, key=lambda x: x['lambda'])
        
        # Extremos
        if lam <= dados_sorted[0]['lambda']:
            return dados_sorted[0]
        if lam >= dados_sorted[-1]['lambda']:
            return dados_sorted[-1]

        # Interpolação
        for i in range(len(dados_sorted) - 1):
            p1 = dados_sorted[i]
            p2 = dados_sorted[i+1]
            
            if p1['lambda'] <= lam <= p2['lambda']:
                t = (lam - p1['lambda']) / (p2['lambda'] - p1['lambda'])
                
                return {
                    "alpha_x": round(p1['alpha_x'] + t * (p2['alpha_x'] - p1['alpha_x']), 3),
                    "alpha_y": round(p1['alpha_y'] + t * (p2['alpha_y'] - p1['alpha_y']), 3),
                    "mu_x": round(p1.get('mu_x', 0.5) + t * (p2.get('mu_x', 0.5) - p1.get('mu_x', 0.5)), 3),
                    "mu_y": round(p1.get('mu_y', 0.5) + t * (p2.get('mu_y', 0.5) - p1.get('mu_y', 0.5)), 3),
                }

        return dados_sorted[0]

    @staticmethod
    def identificar_caso(bordas: Dict[str, str]) -> int:
        engaste_x = list(bordas.values()).count('engastado')
        # ... (lógica simplificada mantida do anterior)
        if engaste_x == 4: return 6
        if engaste_x == 0: return 1
        return 1