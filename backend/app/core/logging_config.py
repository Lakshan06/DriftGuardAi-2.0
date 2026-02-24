"""
Centralized logging configuration for DriftGuardAI backend.
"""
import logging
import logging.handlers
from pathlib import Path

# Create logs directory if it doesn't exist
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Configure root logger
logger = logging.getLogger("driftguard")
logger.setLevel(logging.INFO)

# Console handler - for development and production
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# File handler - for persistent logging
file_handler = logging.handlers.RotatingFileHandler(
    log_dir / "driftguard.log",
    maxBytes=10485760,  # 10MB
    backupCount=5
)
file_handler.setLevel(logging.DEBUG)

# Formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Export logger instance
__all__ = ['logger']
