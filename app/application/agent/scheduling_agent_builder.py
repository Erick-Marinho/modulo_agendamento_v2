from langgraph.graph import StateGraph
from app.application.agent.state.sheduling_agent_state import SchedulingAgentState
from app.application.agent.loaders.node_loader import NodeLoader
from app.application.agent.loaders.edge_loader import EdgeLoader

class SchedulingAgentBuilder:
    """
    Classe responsável por construir o agente de agendamento.
    """

    def __init__(self):
        """
        Inicializa o construtor do agente de agendamento.
        """
        self.agent_graph = StateGraph(SchedulingAgentState)
        self.node_loader = NodeLoader()
        self.edge_loader = EdgeLoader()

    def build_agent(self):
        """
        Constrói e compila o agente de agendamento.
        """
        print("Construindo o grafo do agente...")
        self._add_nodes()
        self._add_edges()
        
        self.agent_graph.set_entry_point("ORCHESTRATOR")
        
        print("Compilando o grafo...")
        return self.agent_graph.compile()

    def _add_nodes(self):
        """
        Adiciona os nós ao grafo de estados.
        """
        nodes = self.node_loader.load_nodes()
        print(f"Adicionando {len(nodes)} nós ao grafo...")
        for name, function in nodes.items():
            self.agent_graph.add_node(name, function)
            print(f"  -> Nó '{name}' adicionado ao grafo")

    def _add_edges(self):
        """
        Adiciona as arestas ao grafo de estados.
        """
        edge_definitions = self.edge_loader.load_edges()
        print(f"Adicionando {len(edge_definitions)} definições de aresta...")
        
        for edge_def in edge_definitions:
            source_node = edge_def.get("source")
            if not source_node:
                continue

            if "condition" in edge_def and "mapping" in edge_def:
                self.agent_graph.add_conditional_edges(
                    source_node,
                    edge_def["condition"],
                    edge_def["mapping"]
                )
                print(f"  -> Aresta condicional de '{source_node}' adicionada")
            elif "destination" in edge_def:
                self.agent_graph.add_edge(
                    source_node,
                    edge_def["destination"]
                )
                print(f"  -> Aresta normal de '{source_node}' para '{edge_def['destination']}' adicionada")

async def get_scheduling_agent():
    """
    Retorna o agente de agendamento compilado.
    """
    builder = SchedulingAgentBuilder()
    return builder.build_agent()