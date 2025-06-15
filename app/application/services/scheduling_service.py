import logging

logger = logging.getLogger(__name__)


class SchedulingService:
    """
    Serviço da camada de aplicação responsável por orquestrar
    o caso de uso de agendamento.
    """

    async def handle_incoming_message(
        self, phone_number: str, message_text: str, message_id: str
    ) -> dict:
        """
        Serviço de agendamento processando mensagem.
        """
        logger.info(f"Serviço de agendamento processando mensagem de {phone_number}.")
        logger.info(f"Conteúdo para análise: '{message_text}'")
        logger.info(f"ID da mensagem: '{message_id}'")

        return {
            "status": "success",
            "message": "Mensagem recebida com sucesso",
            "phone_number": phone_number,
            "message_text": message_text,
            "message_id": message_id,
        }


def get_scheduling_service() -> SchedulingService:
    """
    Provedor de dependência para o SchedulingService.
    O FastAPI chamará esta função para injetar o serviço onde for necessário.
    """
    return SchedulingService()
