from typing import Callable, Tuple
from langchain_core.messages import AIMessage
from app.application.agent.state.sheduling_agent_state import SchedulingAgentState
from app.infrastructure.services.llm.llm_factory import LLMFactory
from app.utils.get_last_message import get_last_message


async def orchestrator_node(state: SchedulingAgentState) -> SchedulingAgentState:
    """
    Nó orquestrador.
    """

    last_message = get_last_message(state)
    
    print("Executando nó orquestrador")
    llm_service = LLMFactory.create_llm_service("openai")
    llm_response = llm_service.orchestrator_prompt_template(last_message)
    
    ai_message = AIMessage(content=llm_response.content)
    
    return {
        **state,
        "messages": [ai_message]
    }


def get_node_definition() -> Tuple[str, Callable]:
    return "ORCHESTRATOR", orchestrator_node
