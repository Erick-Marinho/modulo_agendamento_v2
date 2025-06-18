import logging
from dotenv import load_dotenv
from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.infrastructure.pesistence.postgres_persistence import db_manager
from app.presentation.scheduling_routers import router as message_routers

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Executando o setup da aplicação...")
    
    try:
        # A chamada continua a mesma. A mágica acontece dentro do `initialize_database`.
        await db_manager.initialize_database()
    except Exception as e:
        logger.error(f"❌ Falha crítica durante a inicialização do banco de dados: {e}")

    logger.info("✅ Setup concluído.")
    yield


app = FastAPI(
    title="Agendamento API",
    description="API para agendamento de serviços",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.include_router(message_routers, prefix="/message", tags=["message"])


@app.get("/", summary="Verifica se o servidor está online")
async def root():
    return {
        "status": "API FastAPI está online",
        "version": app.version,
        "docs": "/docs",
    }
