import importlib
import pkgutil
from typing import List, Dict, Any

from app.application.agent import edges


class EdgeLoader:
    """
    Classe responsável por descobrir e carregar dinamicamente as definições
    de arestas do grafo do agente.
    """

    def __init__(self, packages: List[Any] = [edges]):
        """
        Inicializa o carregador de arestas.

        Args:
            packages (List[Any]): Lista de pacotes Python onde as arestas
                                  serão procuradas.
        """
        self.packages = packages
        self.edge_definitions: List[Dict[str, Any]] = []

    def load_edges(self) -> List[Dict[str, Any]]:
        """
        Varre os pacotes, importa os módulos de arestas e carrega suas definições.

        Returns:
            List[Dict[str, Any]]: Uma lista de dicionários, cada um representando
                                  a especificação de uma aresta a ser adicionada
                                  ao grafo.
        """
        if self.edge_definitions:
            return self.edge_definitions

        print("Iniciando descoberta de arestas...")
        for package in self.packages:
            for _, module_name, _ in pkgutil.iter_modules(package.__path__):
                try:
                    module_path = f"{package.__name__}.{module_name}"
                    module = importlib.import_module(module_path)

                    if hasattr(module, "get_edge_definitions"):
                        get_definitions_func = getattr(module, "get_edge_definitions")
                        definitions = get_definitions_func()
                        self.edge_definitions.extend(definitions)
                        print(f"  -> Arestas de '{module_name}' carregadas.")

                except Exception as e:
                    print(f"  [ERRO] Falha ao carregar arestas de '{module_name}': {e}")

        print("Descoberta de arestas finalizada.")
        return self.edge_definitions
