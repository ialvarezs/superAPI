"""
Configuration settings for the supermarket scraping POC
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Supermarket configurations
SUPERMARKETS = {
    'tienda_inglesa': {
        'name': 'Tienda Inglesa',
        'base_url': 'https://www.tiendainglesa.com.uy',
        'lacteos_url': 'https://www.tiendainglesa.com.uy/Institucional/Buscar?categoria=lacteos',
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    },
    'disco': {
        'name': 'Disco',
        'base_url': 'https://www.disco.com.uy',
        'lacteos_url': 'https://www.disco.com.uy/supermercado/lacteos',
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    },
    'devoto': {
        'name': 'Devoto',
        'base_url': 'https://www.devoto.com.uy',
        'lacteos_url': 'https://www.devoto.com.uy/supermercado/lacteos',
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    }
}

# Scraping settings
DELAY_BETWEEN_REQUESTS = 1  # seconds
MAX_RETRIES = 3
TIMEOUT = 30

# Data storage
DATA_DIR = 'data'
RESULTS_DIR = 'results'

# Product matching settings
SIMILARITY_THRESHOLD = 0.8
BARCODE_PATTERNS = [
    r'\b\d{8}\b',      # 8-digit codes
    r'\b\d{12}\b',     # 12-digit UPC
    r'\b\d{13}\b',     # 13-digit EAN
    r'\b\d{14}\b'      # 14-digit codes
]