import json
from typing import Dict, Tuple, Any, List
from pathlib import Path

class TableSolver:
    """
    Implementação dos coeficientes de Marcus/Bares.
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
                print(f"Erro ao carregar tabela de coeficientes: {e}")
                cls._cached_data = {"casos_marcus": {}}

    @staticmethod
    def identificar_caso(bordas: Dict[str, str]) -> int:
        """
        Analisa a topologia das bordas para definir o Caso de Marcus (1 a 6).
        Assumindo Lx = Vão Menor e Ly = Vão Maior.
        """
        # Contagem de engastes
        engastes = sum(1 for v in bordas.values() if v == 'engastado')
        
        if engastes == 0: return 1
        if engastes == 4: return 6
        
        # Identificar posição (Considerando Lx na horizontal e Ly na vertical para simplificação do modelo padrão)
        # Nota: Idealmente verificaríamos qual eixo é o menor, mas vamos assumir orientação padrão da UI
        e_esq = bordas.get('esquerda') == 'engastado'
        e_dir = bordas.get('direita') == 'engastado'
        e_top = bordas.get('topo') == 'engastado'
        e_bot = bordas.get('fundo') == 'engastado'

        if engastes == 1:
            # Caso 2: 1 lado engastado (geralmente o menor para tabelas padrão, mas simplificamos aqui)
            return 2
            
        if engastes == 2:
            # Caso 3: Adjacentes (Canto)
            if (e_esq or e_dir) and (e_top or e_bot):
                return 3
            # Caso 4: Opostos
            return 4
            
        if engastes == 3:
            return 5
            
        return 1 # Fallback

    @staticmethod
    def get_coefficients(caso: int, lam: float) -> Dict[str, float]:
        TableSolver._load_data()
        
        casos = TableSolver._cached_data.get("casos_marcus", {})
        dados_caso = casos.get(str(caso), {}).get("dados", [])
        
        # Fallback se não achar o caso específico
        if not dados_caso:
            # Tenta usar caso 1 (apoiado) como segurança
            dados_caso = casos.get("1", {}).get("dados", [])
            if not dados_caso:
                return {"alpha_x": 10.0, "alpha_y": 10.0 * lam**2, "mu_x": 0.5, "mu_y": 0.5}

        dados_sorted = sorted(dados_caso, key=lambda x: x['lambda'])
        
        if lam <= dados_sorted[0]['lambda']:
            return dados_sorted[0]
        if lam >= dados_sorted[-1]['lambda']:
            return dados_sorted[-1]

        # Interpolação Linear
        for i in range(len(dados_sorted) - 1):
            p1 = dados_sorted[i]
            p2 = dados_sorted[i+1]
            
            if p1['lambda'] <= lam <= p2['lambda']:
                t = (lam - p1['lambda']) / (p2['lambda'] - p1['lambda'])
                return {
                    "alpha_x": p1['alpha_x'] + t * (p2['alpha_x'] - p1['alpha_x']),
                    "alpha_y": p1['alpha_y'] + t * (p2['alpha_y'] - p1['alpha_y']),
                    "mu_x": p1.get('mu_x', 0.5) + t * (p2.get('mu_x', 0.5) - p1.get('mu_x', 0.5)),
                    "mu_y": p1.get('mu_y', 0.5) + t * (p2.get('mu_y', 0.5) - p1.get('mu_y', 0.5)),
                }

        return dados_sorted[0]