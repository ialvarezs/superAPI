"""
Test Tienda Inglesa scraper with 20 products and anti-blocking strategies
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from config import SUPERMARKETS
from scrapers.tienda_inglesa_scraper import TiendaInglesaScraper
from logger import setup_logger
import json

logger = setup_logger('test_tienda_20')

def main():
    logger.info("="*60)
    logger.info("Testing Tienda Inglesa Scraper with 20 products")
    logger.info("Using enhanced anti-blocking strategies")
    logger.info("="*60)
    
    config = SUPERMARKETS['tienda_inglesa']
    
    scraper = TiendaInglesaScraper(
        base_url=config['base_url'],
        category_url=config['arroz_url'],
        headers=config['headers']
    )
    
    # Scrape 20 products
    products = scraper.scrape_category(max_products=20)
    
    logger.info("\n" + "="*60)
    logger.info("RESULTS")
    logger.info("="*60)
    logger.info(f"Total products scraped: {len(products)}")
    logger.info(f"Products with EAN: {sum(1 for p in products if p.get('ean'))}")
    logger.info(f"Products with prices: {sum(1 for p in products if p.get('price'))}")
    
    # Display sample products
    logger.info("\nSample products:")
    for i, p in enumerate(products[:5], 1):
        logger.info(f"\n{i}. {p['name']}")
        logger.info(f"   Price: ${p.get('price', 'N/A')}")
        logger.info(f"   Brand: {p.get('brand', 'N/A')}")
        logger.info(f"   EAN: {p.get('ean', 'N/A')}")
    
    # Save to JSON for inspection
    output_file = f"results/tienda_test_20_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs('results', exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(products, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n✓ Results saved to: {output_file}")
    logger.info("="*60)

if __name__ == "__main__":
    main()
