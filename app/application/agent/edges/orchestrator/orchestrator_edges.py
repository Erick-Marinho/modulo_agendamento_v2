from typing import List, Dict, Any, Literal
from langgraph.graph import END
from app.application.agent.state.sheduling_agent_state import SchedulingAgentState


def get_edge_definitions() -> List[Dict[str, Any]]:
    """
    Retorna as definições de arestas para o nó orquestrador.
    """
    return [
        {
            "source": "ORCHESTRATOR",
            "destination": END
        }
    ]