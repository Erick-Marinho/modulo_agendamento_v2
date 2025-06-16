import importlib
import pkgutil
from typing import Dict, Callable, List
from app.application.agent import node


class NodeLoader:
    """
    Classe responsável por descobrir e carregar dinamicamente os nós do agente.
    """

    def __init__(self, packages: List[str] = [node]):
        """
        Inicializa o carregador de nós.

        Args:
            packages (List[str]): Lista de pacotes onde os nós serão procurados.
        """
        self.packages = packages
        self.nodes: Dict[str, Callable] = {}

    def load_nodes(self) -> Dict[str, Callable]:
        """
        Varre os pacotes, importa os módulos de nós e registra suas definições.

        Este método implementa a lógica de descoberta automática. Ele itera sobre
        os submódulos do pacote 'node', importa-os dinamicamente e busca pela
        função 'get_node_definition' para registrar o nó.

        Returns:
            Dict[str, Callable]: Um dicionário com os nós carregados, mapeando
                                 o nome do nó à sua função executável.
        """
        if self.nodes:
            return self.nodes

        print("Iniciando descoberta de nós...")
        for package in self.packages:
            # pkgutil.iter_modules funciona bem para encontrar todos os submódulos
            for _, module_name, _ in pkgutil.iter_modules(package.__path__):
                try:
                    # Constrói o caminho completo do módulo para importação
                    module_path = f"{package.__name__}.{module_name}.{module_name}_node"

                    # Importa o módulo do nó dinamicamente
                    module = importlib.import_module(module_path)

                    # Busca pela função de definição do nó
                    if hasattr(module, "get_node_definition"):
                        get_node_definition_func = getattr(module, "get_node_definition")
                        node_name, node_function = get_node_definition_func()

                        # Adiciona o nó ao nosso registro
                        self.nodes[node_name] = node_function
                        print(f"  -> Nó '{node_name}' carregado com sucesso.")
                    else:
                        print(
                            f"  [AVISO] Módulo '{module_path}' não possui a função 'get_node_definition'."
                        )

                except ImportError as e:
                    print(f"  [ERRO] Falha ao importar o nó '{module_name}': {e}")
                except Exception as e:
                    print(f"  [ERRO] Erro ao carregar o nó '{module_name}': {e}")

        print("Descoberta de nós finalizada.")
        return self.nodes
