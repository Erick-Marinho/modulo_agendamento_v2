from app.application.agent.state.sheduling_agent_state import SchedulingAgentState


def orchestrator_node(state: SchedulingAgentState) -> SchedulingAgentState:
    """
    Nó orquestrador.
    """
    
    print(state)
    return state