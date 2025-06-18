from typing import Callable, Tuple
from langchain_core.messages import AIMessage
from app.application.agent.state.sheduling_agent_state import SchedulingAgentState
from app.infrastructure.services.llm.llm_factory import LLMFactory
from app.utils.get_last_message import get_last_message


async def orchestrator_node(
    state: SchedulingAgentState,
    config: dict = None
) -> SchedulingAgentState:
    """
    Nó orquestrador.
    """
    
    # Acessar o store via config
    store = None
    if config and "configurable" in config:
        store = config.get("configurable", {}).get("store")

    # memória longo prazo (entre threads)
    user_id = state.get("phone_number")
    last_message = get_last_message(state)
    formatted_memories = "Nenhuma informação prévia sobre este usuário"

    if user_id and store:
        namespace = ("memories", user_id)
        try:
            results = await store.asearch(namespace, query=last_message, limit=5)
            
            if results:
                recalled_data = "\n- ".join([item.value["text"] for item in results])
                formatted_memories = f"O usuário já informou o seguinte:\n- {recalled_data}"
        except Exception as e:
            print(f"Erro ao acessar store: {e}")

    llm_service = LLMFactory.create_llm_service("openai")

    llm_response = llm_service.orchestrator_prompt_template(last_message, formatted_memories)

    ai_message = AIMessage(content=llm_response.content)

    return {"messages": [ai_message]}


def get_node_definition() -> Tuple[str, Callable]:
    return "ORCHESTRATOR", orchestrator_node