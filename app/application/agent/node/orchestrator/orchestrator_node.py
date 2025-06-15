from typing import Callable, Tuple
from app.application.agent.state.sheduling_agent_state import SchedulingAgentState

def orchestrator_node(state: SchedulingAgentState) -> SchedulingAgentState:
    """
    Nó orquestrador.
    """

    print("Executando nó orquestrador")
    return state

def get_node_definition() -> Tuple[str, Callable]:
    return "ORCHESTRATOR", orchestrator_node