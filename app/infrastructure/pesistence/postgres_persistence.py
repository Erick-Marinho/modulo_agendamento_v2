import asyncio
import asyncpg
import json
from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres import AsyncPostgresStore
from app.infrastructure.config.config import settings


# Variáveis globais
checkpointer = None
store = None
connection_pool = None

# URI PostgreSQL
postgres_uri = (
    f"postgresql://"
    f"{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD.get_secret_value()}"
    f"@db:5432/{settings.POSTGRES_DB}"
)

async def get_connection_pool():
    """Cria e retorna o pool de conexões"""
    global connection_pool
    if connection_pool is None:
        connection_kwargs = {
            "autocommit": True,
            "prepare_threshold": 0,
            "row_factory": dict_row,
        }
        
        connection_pool = AsyncConnectionPool(
            conninfo=postgres_uri,
            max_size=20,
            kwargs=connection_kwargs
        )
        await connection_pool.open()
    return connection_pool

async def get_checkpointer():
    """Retorna checkpointer PostgreSQL com pool"""
    global checkpointer
    if checkpointer is None:
        pool = await get_connection_pool()
        checkpointer = AsyncPostgresSaver(pool)
    return checkpointer

async def get_store():
    """Retorna store PostgreSQL com pool"""
    global store
    if store is None:
        pool = await get_connection_pool()
        store = AsyncPostgresStore(pool)
    return store

async def setup_persistence():
    """Setup inicial das tabelas PostgreSQL com tratamento de erro"""
    try:
        pool = await get_connection_pool()
        async with pool.connection() as conn:
            setup_checkpointer = AsyncPostgresSaver(conn)
            await setup_checkpointer.setup()
        
        print("✅ Tabelas PostgreSQL criadas:")
        print("  📝 checkpoints")
        print("  📝 checkpoint_writes")
        print("  💾 Persistência REAL ativada!")
        
    except Exception as e:
        print(f"❌ Erro no setup do LangGraph: {e}")
        print("💡 Execute: POST /api/debug/reset-langgraph-tables")
        # Não falhar a aplicação por causa disso
        pass

async def create_custom_tables():
    """📋 Criar todas as tabelas customizadas"""
    try:
        conn = await asyncpg.connect(
            host="db", port=5432,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD.get_secret_value(),
            database=settings.POSTGRES_DB
        )
        
        try:
            # Tabela de conversas
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(50) NOT NULL,
                    message TEXT NOT NULL,
                    response TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Tabela de agendamentos
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS appointments (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(50) NOT NULL,
                    specialty VARCHAR(100),
                    professional VARCHAR(100),
                    date_scheduled DATE,
                    time_scheduled TIME,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Tabela de memórias do usuário
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_memories (
                    user_id VARCHAR(50) PRIMARY KEY,
                    memory_data JSONB,
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Tabela de histórico de conversas
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS conversation_history (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(50) NOT NULL,
                    message_text TEXT,
                    response_text TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Tabela de agendamentos completos
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS completed_appointments (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(50) NOT NULL,
                    appointment_data JSONB,
                    completed_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            print("✅ Todas as tabelas customizadas criadas:")
            print("  📋 conversations")
            print("  📋 appointments") 
            print("  📋 user_memories")
            print("  📋 conversation_history")
            print("  📋 completed_appointments")
            
        finally:
            await conn.close()
            
    except Exception as e:
        print(f"❌ Erro ao criar tabelas customizadas: {e}")

# Funções simples com AsyncPG
async def save_conversation(user_id: str, message: str, response: str):
    """Salva conversa"""
    try:
        conn = await asyncpg.connect(
            host="db", port=5432,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD.get_secret_value(),
            database=settings.POSTGRES_DB
        )
        
        await conn.execute(
            "INSERT INTO conversations (user_id, message, response) VALUES ($1, $2, $3)",
            user_id, message, response
        )
        
        await conn.close()
        print(f"💾 Conversa salva: {user_id}")
    except Exception as e:
        print(f"Erro ao salvar: {e}")

async def save_appointment(user_id: str, specialty: str, professional: str, date_scheduled: str, time_scheduled: str):
    """Salva agendamento"""
    try:
        conn = await asyncpg.connect(
            host="db", port=5432,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD.get_secret_value(),
            database=settings.POSTGRES_DB
        )
        
        await conn.execute(
            "INSERT INTO appointments (user_id, specialty, professional, date_scheduled, time_scheduled) VALUES ($1, $2, $3, $4, $5)",
            user_id, specialty, professional, date_scheduled, time_scheduled
        )
        
        await conn.close()
        print(f"✅ Agendamento salvo: {user_id}")
    except Exception as e:
        print(f"Erro: {e}")

# Funções para salvar dados (mantidas + novas)
async def save_conversation_message(user_id: str, message_id: str, human_content: str, 
                                  ai_content: str, scheduling_data: dict = None):
    """💾 Salva mensagem de conversa corretamente"""
    try:
        conn = await asyncpg.connect(
            host="db", port=5432,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD.get_secret_value(),
            database=settings.POSTGRES_DB
        )
        
        try:
            await conn.execute("""
                INSERT INTO conversations (user_id, message, response, created_at) 
                VALUES ($1, $2, $3, NOW())
            """, user_id, human_content, ai_content)
            
            print(f"💾 Conversa salva: {user_id} - {human_content[:50]}...")
        finally:
            await conn.close()
            
    except Exception as e:
        print(f"❌ Erro ao salvar conversa: {e}")

async def save_agent_state(user_id: str, session_id: str, node_name: str, 
                          state_data: dict, execution_time_ms: int = None):
    """Salva estado do agente (simulação manual do checkpoint)"""
    import json
    
    try:
        async with asyncpg.connect(
            host="db",
            port=5432,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD.get_secret_value(),
            database=settings.POSTGRES_DB
        ) as conn:
            await conn.execute(
                "INSERT INTO conversations (user_id, message, response) VALUES ($1, $2, $3)",
                user_id, json.dumps(state_data), None
            )
            await conn.execute(
                "UPDATE conversations SET response = $1 WHERE user_id = $2",
                json.dumps(state_data), user_id
            )
            await conn.close()
        print(f"🤖 Estado do agente salvo: {user_id} - {node_name}")
    except Exception as e:
        print(f"Erro ao salvar estado: {e}")

async def save_completed_appointment(user_id: str, appointment_data: dict):
    """✅ Salva agendamento completo"""
    try:
        conn = await asyncpg.connect(
            host="db", port=5432,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD.get_secret_value(),
            database=settings.POSTGRES_DB
        )
        
        try:
            await conn.execute("""
                INSERT INTO appointments (user_id, specialty, professional, date_scheduled, time_scheduled) 
                VALUES ($1, $2, $3, $4, $5)
            """, 
                user_id,
                appointment_data.get('specialty'),
                appointment_data.get('professional_name'),
                appointment_data.get('date_scheduled'),
                appointment_data.get('specific_time')
            )
            
            print(f"✅ Agendamento salvo: {user_id}")
        finally:
            await conn.close()
            
    except Exception as e:
        print(f"❌ Erro ao salvar agendamento: {e}")

# Funções de análise (novas!)
async def get_conversation_analytics(user_id: str = None):
    """Analytics detalhadas das conversas"""
    try:
        async with asyncpg.connect(
            host="db",
            port=5432,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD.get_secret_value(),
            database=settings.POSTGRES_DB
        ) as conn:
            if user_id:
                await conn.execute("""
                    SELECT messages_count, appointment_completed, 
                           specialty_requested, success_rate, session_start, session_end
                    FROM conversations 
                    WHERE user_id = $1
                """, (user_id,))
            else:
                await conn.execute("""
                    SELECT COUNT(*) as total_users,
                           SUM(messages_count) as total_messages,
                           COUNT(CASE WHEN appointment_completed THEN 1 END) as completed_appointments,
                           AVG(success_rate) as avg_success_rate
                    FROM conversations
                """)
            
            return await conn.fetchall()
    except Exception as e:
        print(f"Erro ao buscar analytics: {e}")
        return []

async def get_agent_execution_analytics():
    """Analytics de performance do agente"""
    try:
        async with asyncpg.connect(
            host="db",
            port=5432,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD.get_secret_value(),
            database=settings.POSTGRES_DB
        ) as conn:
            await conn.execute("""
                SELECT node_name,
                       COUNT(*) as executions,
                       AVG(execution_time_ms) as avg_time_ms,
                       MAX(execution_time_ms) as max_time_ms,
                       MIN(execution_time_ms) as min_time_ms
                FROM conversations 
                WHERE execution_time_ms IS NOT NULL
                GROUP BY node_name
                ORDER BY avg_time_ms DESC
            """)
            
            return await conn.fetchall()
    except Exception as e:
        print(f"Erro ao buscar analytics de execução: {e}")
        return []

async def save_user_memory(user_id: str, memory_data: dict):
    """💭 Salva memórias/preferências do usuário"""
    import json
    try:
        conn = await asyncpg.connect(
            host="db", port=5432,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD.get_secret_value(),
            database=settings.POSTGRES_DB
        )
        
        try:
            await conn.execute("""
                INSERT INTO user_memories (user_id, memory_data, updated_at) 
                VALUES ($1, $2, NOW())
                ON CONFLICT (user_id) 
                DO UPDATE SET memory_data = $2, updated_at = NOW()
            """, user_id, json.dumps(memory_data))
            
            print(f"💭 Memória salva: {user_id}")
        finally:
            await conn.close()
            
    except Exception as e:
        print(f"Erro ao salvar memória: {e}")

async def get_user_conversation_history(user_id: str, limit: int = 50):
    """📜 Busca histórico de conversas do usuário"""
    try:
        conn = await asyncpg.connect(
            host="db", port=5432,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD.get_secret_value(),
            database=settings.POSTGRES_DB
        )
        
        try:
            rows = await conn.fetch("""
                SELECT message, response, created_at
                FROM conversations 
                WHERE user_id = $1 
                ORDER BY created_at DESC 
                LIMIT $2
            """, user_id, limit)
            
            return [dict(row) for row in rows]
        finally:
            await conn.close()
            
    except Exception as e:
        print(f"Erro ao buscar histórico: {e}")
        return []

async def get_checkpoint_summary(thread_id: str = None):
    """🔍 Analisa dados dos checkpoints do LangGraph - CORRIGIDO"""
    try:
        conn = await asyncpg.connect(
            host="db", port=5432,
            user=settings.POSTGRES_USER,  
            password=settings.POSTGRES_PASSWORD.get_secret_value(),
            database=settings.POSTGRES_DB
        )
        
        try:
            if thread_id:
                rows = await conn.fetch("""
                    SELECT thread_id, checkpoint_id, 
                           LENGTH(checkpoint) as checkpoint_size
                    FROM checkpoints 
                    WHERE thread_id = $1 
                    ORDER BY created_at DESC
                """, thread_id)
            else:
                rows = await conn.fetch("""
                    SELECT thread_id, COUNT(*) as checkpoint_count,
                           SUM(LENGTH(checkpoint)) as total_data_size
                    FROM checkpoints 
                    GROUP BY thread_id
                    ORDER BY thread_id
                """)
            
            return [dict(row) for row in rows]
        finally:
            await conn.close()
            
    except Exception as e:
        print(f"❌ Erro ao analisar checkpoints: {e}")
        return []

async def save_conversation_with_unique_id(user_id: str, unique_message_id: str, 
                                         human_content: str, ai_content: str, 
                                         scheduling_data: dict = None):
    """💾 Salva com ID único (evita duplicação)"""
    try:
        conn = await asyncpg.connect(
            host="db", port=5432,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD.get_secret_value(),
            database=settings.POSTGRES_DB
        )
        
        try:
            # Inserir apenas se message_id não existir
            await conn.execute("""
                INSERT INTO conversations (user_id, message, response, created_at) 
                SELECT $1, $2, $3, NOW()
                WHERE NOT EXISTS (
                    SELECT 1 FROM conversations 
                    WHERE user_id = $1 AND message = $2 AND response = $3
                )
            """, user_id, human_content, ai_content)
            
            print(f"💾 Conversa única salva: {user_id}")
        finally:
            await conn.close()
            
    except Exception as e:
        print(f"❌ Erro ao salvar conversa única: {e}")

async def save_conversation_simple(user_id: str, human_content: str, ai_content: str):
    """💾 Salva conversa com DEBUG completo"""
    try:
        print(f"🔍 DEBUG: Tentando conectar no banco...")
        
        conn = await asyncpg.connect(
            host="db", port=5432,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD.get_secret_value(),
            database=settings.POSTGRES_DB
        )
        
        print(f"🔍 DEBUG: Conexão estabelecida")
        
        try:
            print(f"🔍 DEBUG: Executando INSERT para {user_id}")
            
            result = await conn.execute("""
                INSERT INTO conversations (user_id, message, response, created_at) 
                VALUES ($1, $2, $3, NOW())
            """, user_id, human_content, ai_content)
            
            print(f"🔍 DEBUG: INSERT executado: {result}")
            print(f"💾 Conversa salva: {user_id} - {human_content[:30]}...")
            
        finally:
            await conn.close()
            print(f"🔍 DEBUG: Conexão fechada")
            
    except Exception as e:
        print(f"❌ DEBUG: Erro detalhado ao salvar conversa: {e}")
        import traceback
        traceback.print_exc()