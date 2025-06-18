import logging
from langchain_core.messages import HumanMessage, AIMessage
from fastapi import Depends
from app.application.agent.scheduling_agent_builder import get_scheduling_agent
from app.domain.scheduling_data import SchedulingData
from app.infrastructure.pesistence.postgres_persistence import (
    save_conversation_message,
    save_completed_appointment,
    save_user_memory,
    save_conversation_simple
)

logger = logging.getLogger(__name__)


class SchedulingService:
    """
    Serviço da camada de aplicação responsável por orquestrar
    o caso de uso de agendamento.
    """

    def __init__(self, scheduling_agent):
        """
        Inicializa o serviço de agendamento.
        """
        self.scheduling_agent = scheduling_agent

    async def handle_incoming_message(
        self, phone_number: str, message_text: str, message_id: str
    ) -> dict:
        """
        Serviço de agendamento processando mensagem.
        """
        logger.info(f"🔍 DEBUG: handle_incoming_message iniciado para {phone_number}")
        logger.info(f"Serviço de agendamento processando mensagem de {phone_number}.")
        logger.info(f"Conteúdo para análise: '{message_text}'")
        logger.info(f"ID da mensagem: '{message_id}'")

        try:
            thread_id = phone_number
            config = {"configurable": {"thread_id": thread_id}}

            initial_state = {
                "phone_number": phone_number,
                "message_id": message_id,
                "messages": [HumanMessage(content=message_text)],
                "scheduling_data": SchedulingData(),
            }

            final_state = await self.scheduling_agent.ainvoke(
                initial_state, config=config
            )

            logger.info(
                f"Processamento do agente concluído. Estado final: {final_state}"
            )

            messages = final_state.get("messages", [])
            scheduling_data = final_state.get("scheduling_data", SchedulingData())

            logger.info(f"🔍 DEBUG: Chamando _persist_conversation...")
            
            # 📝 PERSISTIR CONVERSA COMPLETA
            await self._persist_conversation(
                phone_number, messages, scheduling_data, message_id
            )
            
            logger.info(f"🔍 DEBUG: _persist_conversation concluída")

            last_message = messages[-1]

            return {
                "status": "success",
                "message": last_message.content,
                "scheduling_data": scheduling_data.dict() if hasattr(scheduling_data, 'dict') else str(scheduling_data)
            }

        except Exception as e:
            logger.error(f"Erro ao processar mensagem com agente: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Erro ao processar mensagem com agente: {e}",
            }

    async def _persist_conversation(self, phone_number: str, messages: list, 
                                  scheduling_data, message_id: str):
        """💾 Versão com DEBUG completo"""
        try:
            from app.infrastructure.pesistence.postgres_persistence import save_conversation_simple
            
            logger.info(f"🔍 DEBUG: _persist_conversation chamada para {phone_number}")
            logger.info(f"🔍 DEBUG: Total de mensagens: {len(messages)}")
            
            if len(messages) >= 2:
                last_human = messages[-2]
                last_ai = messages[-1]
                
                logger.info(f"🔍 DEBUG: Última human: {type(last_human)} - {last_human.content[:50]}...")
                logger.info(f"🔍 DEBUG: Última AI: {type(last_ai)} - {last_ai.content[:50]}...")
                
                if (isinstance(last_human, HumanMessage) and 
                    isinstance(last_ai, AIMessage)):
                    
                    logger.info(f"🔍 DEBUG: Tentando salvar conversa...")
                    
                    # Salvar - duplicatas serão ignoradas pelo banco
                    await save_conversation_simple(
                        phone_number,
                        last_human.content,
                        last_ai.content
                    )
                    
                    logger.info(f"💾 DEBUG: Conversa salva com sucesso: {phone_number}")
                else:
                    logger.warning(f"❌ DEBUG: Tipos incorretos das mensagens")
            else:
                logger.warning(f"❌ DEBUG: Menos de 2 mensagens no array")
            
        except Exception as e:
            logger.error(f"❌ DEBUG: Erro ao persistir: {e}", exc_info=True)


def get_scheduling_service(agent=Depends(get_scheduling_agent)) -> SchedulingService:
    """
    Provedor de dependência para o SchedulingService.
    O FastAPI chamará esta função para injetar o serviço onde for necessário.
    """
    return SchedulingService(scheduling_agent=agent)
