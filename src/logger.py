import logging

from .settings import settings

logger = logging.getLogger("highkey_backend")
logger.setLevel(settings.LOG_LEVEL)

formatter = logging.Formatter("[%(asctime)s][%(name)s][%(levelname)s]: %(message)s")

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

settings.LOG_DIR.mkdir(parents=True, exist_ok=True)
file_handler = logging.FileHandler(settings.LOG_DIR / "highkey_backend.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
