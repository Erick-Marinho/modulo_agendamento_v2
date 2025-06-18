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

@router.get("/conversations/{user_id}")
async def get_user_conversations(user_id: str):
    """📊 Visualizar conversas de um usuário"""
    from app.infrastructure.pesistence.postgres_persistence import (
        get_user_conversation_history, get_checkpoint_summary
    )
    
    conversations = await get_user_conversation_history(user_id)
    checkpoints = await get_checkpoint_summary(user_id)
    
    return {
        "user_id": user_id,
        "conversation_history": conversations,
        "checkpoint_summary": checkpoints
    }

@router.get("/debug/database")
async def debug_database():
    """🔍 Debug: verificar todas as tabelas"""
    import asyncpg
    from app.infrastructure.config.config import settings
    
    try:
        conn = await asyncpg.connect(
            host="db", port=5432,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD.get_secret_value(),
            database=settings.POSTGRES_DB
        )
        
        try:
            # Listar todas as tabelas
            tables = await conn.fetch("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            
            # Contar registros em cada tabela
            counts = {}
            for table in tables:
                table_name = table['table_name']
                try:
                    count = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
                    counts[table_name] = count
                except:
                    counts[table_name] = "Error"
            
            return {
                "tables": [t['table_name'] for t in tables],
                "record_counts": counts
            }
        finally:
            await conn.close()
            
    except Exception as e:
        return {"error": str(e)}
    
@router.post("/debug/truncate-tables")
async def truncate_custom_tables():
    """🗑️ Truncar todas as tabelas customizadas"""
    import asyncpg
    from app.infrastructure.config.config import settings
    
    try:
        conn = await asyncpg.connect(
            host="db", port=5432,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD.get_secret_value(),
            database=settings.POSTGRES_DB
        )
        
        try:
            # Truncar tabelas customizadas
            await conn.execute("TRUNCATE TABLE conversations RESTART IDENTITY CASCADE")
            await conn.execute("TRUNCATE TABLE appointments RESTART IDENTITY CASCADE")
            await conn.execute("TRUNCATE TABLE completed_appointments RESTART IDENTITY CASCADE")
            await conn.execute("TRUNCATE TABLE conversation_history RESTART IDENTITY CASCADE")
            await conn.execute("TRUNCATE TABLE user_memories RESTART IDENTITY CASCADE")
            await conn.execute("TRUNCATE TABLE checkpoints RESTART IDENTITY CASCADE")
            await conn.execute("TRUNCATE TABLE checkpoint_writes RESTART IDENTITY CASCADE")
            await conn.execute("TRUNCATE TABLE user_memories RESTART IDENTITY CASCADE")
            await conn.execute("TRUNCATE TABLE checkpoint_blobs RESTART IDENTITY CASCADE")
            await conn.execute("TRUNCATE TABLE checkpoint_migrations RESTART IDENTITY CASCADE")
            
            # Verificar resultado
            counts = {}
            tables = ['conversations', 'appointments', 'completed_appointments', 
                     'conversation_history', 'user_memories', 'checkpoints', 'checkpoint_writes', 'checkpoint_blobs', 'conversation_history', 'checkpoint_migrations']
            
            for table in tables:
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                counts[table] = count
            
            return {
                "message": "✅ Tabelas truncadas com sucesso",
                "record_counts": counts
            }
        finally:
            await conn.close()
            
    except Exception as e:
        return {"error": str(e)}