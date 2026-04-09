import sys
from loguru import logger

def setup_logger(debug: bool = False):
    logger.remove()
    level = "DEBUG" if debug else "INFO"
    
    # Console logger
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=level,
    )
    
    # File logger for debugging and history
    logger.add(
        "logs/ai_crawler_{time}.log",
        rotation="10 MB",
        retention="10 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    )

    return logger

# Default logger instance
log = logger
