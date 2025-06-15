from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from app.application.agent.state.sheduling_agent_state import SchedulingAgentState


class SchedulingAgentBuilder:
    """
    Classe responsável por construir o agente de agendamento.
    """

    # Inicialização do grafo de estados
    def __init__(self):
        """
        Inicializa o grafo de estados.
        """

        self.agent_graph = StateGraph(SchedulingAgentState)

    def _build_graph(self):
        """
        Constrói o grafo de estados.
        """

        self._add_nodes()
        self.agent_graph.set_entry_point(START)
        self._add_edges()

        pass

    def _add_nodes(self):
        """
        Adiciona os nós ao grafo de estados.
        """
        pass

    def _add_edges(self):
        """
        Adiciona as arestas ao grafo de estados.
        """
        pass

    def build_agent(self):
        """
        Constrói o agente de agendamento.
        """
        pass


async def get_scheduling_agent():
    """
    Retorna o agente de agendamento.
    """
    pass