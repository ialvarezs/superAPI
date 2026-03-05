"""
Centralized logging system for scraping operations
"""
import logging
import os
from datetime import datetime

def setup_logger(name: str, log_file: str = None, level=logging.INFO):
    """Setup logger with file and console handlers"""
    
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File handler
    if log_file is None:
        log_file = f'logs/{name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str):
    """Get existing logger or create new one"""
    return logging.getLogger(name)
