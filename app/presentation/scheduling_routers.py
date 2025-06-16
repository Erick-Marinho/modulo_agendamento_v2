import logging
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, status, Depends
from app.presentation.dto.message_request_payload import WebhookPayload
from app.application.services.scheduling_service import (
    get_scheduling_service,
    SchedulingService,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class MessageRequest(BaseModel):
    message: str


@router.post("/", summary="Recebe mensagem do webhook", status_code=status.HTTP_200_OK)
async def receive_webhook(
    payload: WebhookPayload, service: SchedulingService = Depends(get_scheduling_service)
):
    logger.info(f"Nova mensagem de '{payload.phone_number}' recebida.")
    logger.info(f"Conteúdo: '{payload.message}'")

    result = await service.handle_incoming_message(
        payload.phone_number, payload.message, payload.message_id
    )

    return result
