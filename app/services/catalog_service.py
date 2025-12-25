import json
from typing import List, Dict, Any, Optional
from config.settings import CATALOG_PATH

class CatalogService:
    """
    Serviço responsável por carregar e gerir os dados dos catálogos comerciais.
    Lida com bitolas de aço, elementos de enchimento e modelos de treliças.
    """

    def __init__(self):
        self._data: Dict[str, Any] = self._load_json()

    def _load_json(self) -> Dict[str, Any]:
        """Lê o ficheiro JSON de catálogos definido nas definições."""
        try:
            if not CATALOG_PATH.exists():
                print(f"Aviso: Ficheiro de catálogo não encontrado em {CATALOG_PATH}")
                return {}
            
            with open(CATALOG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"Erro ao processar JSON de catálogos: {e}")
            return {}
        except Exception as e:
            print(f"Erro inesperado ao carregar catálogos: {e}")
            return {}

    def reload(self):
        """Recarrega os dados do ficheiro (útil se o JSON for editado em runtime)."""
        self._data = self._load_json()

    # --- Métodos para Aço (Bitolas) ---

    def get_todas_bitolas(self) -> List[Dict[str, Any]]:
        """Retorna a lista completa de bitolas disponíveis."""
        return self._data.get("bitolas_padrao", [])

    def get_bitola_por_id(self, bitola_id: str) -> Optional[Dict[str, Any]]:
        """Busca uma bitola específica (ex: '10.0')."""
        bitolas = self.get_todas_bitolas()
        return next((b for b in bitolas if b["id"] == bitola_id), None)

    # --- Métodos para Enchimento (Lajotas/EPS) ---

    def get_todos_enchimentos(self) -> List[Dict[str, Any]]:
        """Retorna todos os elementos de enchimento do catálogo."""
        return self._data.get("elementos_enchimento", [])

    def get_enchimentos_por_tipo(self, tipo: str) -> List[Dict[str, Any]]:
        """Filtra enchimentos por tipo: 'CERAMICA' ou 'EPS'."""
        return [e for e in self.get_todos_enchimentos() if e["tipo"] == tipo.upper()]

    def get_modelo_enchimento(self, modelo: str) -> Optional[Dict[str, Any]]:
        """Busca os dados técnicos de um modelo específico de enchimento."""
        enchimentos = self.get_todos_enchimentos()
        return next((e for e in enchimentos if e["modelo"] == modelo), None)

    # --- Métodos para Treliças ---

    def get_modelos_trelica(self) -> List[Dict[str, Any]]:
        """Retorna a lista de treliças padrão (TR8, TR12, etc)."""
        return self._data.get("truss_standard", [])

    def get_trelica_por_modelo(self, modelo: str) -> Optional[Dict[str, Any]]:
        """Busca os dados de geometria de uma treliça pelo nome do modelo."""
        modelos = self.get_modelos_trelica()
        return next((m for m in modelos if m["modelo"] == modelo), None)

    # --- Métodos de Configuração de Nervura ---

    def get_config_nervura(self) -> Dict[str, float]:
        """Retorna as configurações padrão de geometria da nervura/sapata."""
        return self._data.get("configuracoes_nervura", {
            "largura_sapata_padrao_cm": 12.5,
            "espessura_sapata_cm": 3.0
        })

# Instância global para ser importada por outros módulos (Padrão Singleton facilitado)
catalog_service = CatalogService()