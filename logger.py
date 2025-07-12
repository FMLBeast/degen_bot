import logging
from logging.handlers import RotatingFileHandler
from config import LOG_PATH, LOG_LEVEL

handler = RotatingFileHandler(LOG_PATH, maxBytes=10_000_000, backupCount=5)
handler.namer = lambda n: f"{n}.immutable"

logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[handler]
)
logger = logging.getLogger('wallet')
