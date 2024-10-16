import os
from dotenv import load_dotenv
import logging
import urllib.parse
from sqlalchemy.ext.declarative import declarative_base

load_dotenv()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Configurações do banco de dados
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')

logger.debug(f"DB_USER: {DB_USER}")
logger.debug(f"DB_HOST: {DB_HOST}")
logger.debug(f"DB_NAME: {DB_NAME}")

if DB_PASSWORD is None:
    raise ValueError("DB_PASSWORD não está definido no arquivo .env")

# String de conexão para o MySQL
PASSWORD_ENCODED = urllib.parse.quote_plus(DB_PASSWORD.encode('utf-8'))
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{PASSWORD_ENCODED}@{DB_HOST}/{DB_NAME}?connect_timeout=30"

logger.debug(f"DATABASE_URL (com senha oculta): {DATABASE_URL.replace(PASSWORD_ENCODED, '********')}")

# Configurações SSL
ssl_args = {
    "ssl_ca": os.path.join(os.path.dirname(__file__), "ssl_certs", "server-ca.pem"),
    "ssl_cert": os.path.join(os.path.dirname(__file__), "ssl_certs", "client-cert.pem"),
    "ssl_key": os.path.join(os.path.dirname(__file__), "ssl_certs", "client-key.pem")
}

# Criar a base declarativa
Base = declarative_base()
