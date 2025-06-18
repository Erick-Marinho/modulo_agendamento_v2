import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI

from app.presentation.scheduling_routers import router as message_routers
from app.infrastructure.pesistence.postgres_persistence import (
    setup_persistence, 
    create_custom_tables
)

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Executando setup de persistência PostgreSQL...")
    
    try:
        await setup_persistence()
    except Exception as e:
        logger.error(f"❌ Erro no setup LangGraph: {e}")
        logger.info("💡 Execute POST /api/debug/reset-langgraph-tables e reinicie")
    
    try:
        await create_custom_tables()
        logger.info("✅ Tabelas customizadas criadas!")
    except Exception as e:
        logger.error(f"❌ Erro nas tabelas customizadas: {e}")
    
    logger.info("✅ Setup concluído (com ou sem erros)")
    yield


app = FastAPI(
    title="Agendamento API",
    description="API para agendamento de serviços",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.include_router(message_routers, prefix="/api")


@app.get("/", summary="Verifica se o servidor está online")
async def root():
    return {
        "status": "API FastAPI está online",
        "version": app.version,
        "docs": "/docs",
    }
