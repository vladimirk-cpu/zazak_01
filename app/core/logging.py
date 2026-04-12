import logging
from logging.handlers import RotatingFileHandler
import os
from app.core.config import settings

def setup_logging():
    log_dir = settings.LOG_FILE_PATH

    logger = logging.getLogger("app")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # App log
    app_handler = RotatingFileHandler(
        os.path.join(log_dir, "app.log"), maxBytes=10*1024*1024, backupCount=5
    )
    app_handler.setFormatter(formatter)
    
    # Error log
    error_handler = RotatingFileHandler(
        os.path.join(log_dir, "error.log"), maxBytes=10*1024*1024, backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    # Stdout
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(app_handler)
        logger.addHandler(error_handler)
        logger.addHandler(stream_handler)
        
    return logger

logger = setup_logging()
