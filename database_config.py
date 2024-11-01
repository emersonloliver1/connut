import os
from dotenv import load_dotenv
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

load_dotenv()
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Configurações do Supabase PostgreSQL
DB_USER = os.getenv('SUPABASE_DB_USER')
DB_PASSWORD = os.getenv('SUPABASE_DB_PASSWORD')
DB_HOST = os.getenv('SUPABASE_DB_HOST')
DB_NAME = os.getenv('SUPABASE_DB_NAME')
DB_PORT = os.getenv('SUPABASE_DB_PORT', '5432')

if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_NAME]):
    raise ValueError("Todas as variáveis de ambiente do Supabase devem estar definidas")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

logger.debug(f"DATABASE_URL (com senha oculta): {DATABASE_URL.replace(DB_PASSWORD, '********')}")

# Configurações SSL para conexão segura
ssl_args = {
    "sslmode": "require"
}

# Criar a base declarativa
Base = declarative_base()
