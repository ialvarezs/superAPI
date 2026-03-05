"""
Master orchestrator - runs all scrapers and generates reports
"""
import sys
import os
from datetime import datetime
from typing import Dict, List

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import time
from config import SUPERMARKETS
from database import ProductDatabase
from scrapers.playwright_scraper import PlaywrightScraper
from scrapers.search_scraper import SearchBasedScraper
from scrapers.tienda_inglesa_scraper import TiendaInglesaScraper
from enhanced_matcher import EnhancedProductMatcher
from report_generator import ReportGenerator
from logger import setup_logger

logger = setup_logger('master_orchestrator')

class MasterOrchestrator:
    """Orchestrate complete scraping pipeline"""
    
    def __init__(self, db_path: str = "data/arroz_complete.db"):
        self.db = ProductDatabase(db_path)
        self.matcher = EnhancedProductMatcher(similarity_threshold=0.75)
        self.reporter = ReportGenerator()
        self.products_by_store = {}
        
        logger.info(f"Initialized orchestrator with database: {db_path}")
    
    def run_complete_pipeline(self):
        """Run complete scraping and matching pipeline"""
        start_time = datetime.now()
        logger.info("="*60)
        logger.info("STARTING COMPLETE SCRAPING PIPELINE")
        logger.info(f"Start time: {start_time}")
        logger.info("="*60)
        
        # Phase 1: Scrape all supermarkets
        logger.info("\n### PHASE 1: SCRAPING ALL SUPERMARKETS ###\n")
        self._scrape_all_supermarkets()
        
        # Phase 2: Match products
        logger.info("\n### PHASE 2: MATCHING PRODUCTS ###\n")
        matches = self._match_all_products()
        
        # Phase 3: Save to database
        logger.info("\n### PHASE 3: SAVING TO DATABASE ###\n")
        self._save_to_database(matches)
        
        # Phase 4: Generate reports
        logger.info("\n### PHASE 4: GENERATING REPORTS ###\n")
        self._generate_reports(matches)
        
        # Final summary
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.info("="*60)
        logger.info("PIPELINE COMPLETED SUCCESSFULLY")
        logger.info(f"End time: {end_time}")
        logger.info(f"Duration: {duration}")
        logger.info(f"Total products: {sum(len(p) for p in self.products_by_store.values())}")
        logger.info(f"Total matches: {len(matches)}")
        logger.info("="*60)
    
    def _scrape_all_supermarkets(self):
        """Scrape all configured supermarkets"""
        
        for store_key, config in SUPERMARKETS.items():
            try:
                logger.info(f"\n--- Scraping {config['name']} ---")
                
                if store_key == 'tienda_inglesa':
                    scraper = TiendaInglesaScraper(
                        base_url=config['base_url'],
                        category_url=config['arroz_url'],
                        headers=config['headers']
                    )
                    # Limit to 20 products for testing with anti-blocking
                    products = scraper.scrape_category(max_products=20)
                elif store_key == 'tata':
                    # Tata uses proper category URL
                    scraper = PlaywrightScraper(
                        supermarket=store_key,
                        base_url=config['base_url'],
                        category_url=config['arroz_url']
                    )
                    products = scraper.scrape_category()
                else:
                    # Disco, Devoto, Geant - use category pages with Playwright
                    scraper = PlaywrightScraper(
                        supermarket=store_key,
                        base_url=config['base_url'],
                        category_url=config['arroz_url']
                    )
                    products = scraper.scrape_category()
                
                if store_key != 'tienda_inglesa':
                    products = scraper.scrape_category()
                
                self.products_by_store[store_key] = products
                
                logger.info(f"✓ {config['name']}: {len(products)} products scraped")
                
                # Short delay between stores
                time.sleep(3)
                
            except Exception as e:
                logger.error(f"✗ Failed to scrape {config['name']}: {e}")
                self.products_by_store[store_key] = []
    
    def _match_all_products(self) -> List[Dict]:
        """Match products across all stores"""
        try:
            matches = self.matcher.match_products(self.products_by_store)
            logger.info(f"Matching complete: {len(matches)} matches found")
            return matches
        except Exception as e:
            logger.error(f"Error in matching: {e}")
            return []
    
    def _save_to_database(self, matches: List[Dict]):
        """Save all products and matches to database"""
        try:
            # Save products
            for store, products in self.products_by_store.items():
                count = self.db.save_products(products, store)
                logger.info(f"Saved {count} products from {store} to database")
            
            # Save matches
            if matches:
                count = self.db.save_matches(matches)
                logger.info(f"Saved {count} matches to database")
            
        except Exception as e:
            logger.error(f"Error saving to database: {e}")
    
    def _generate_reports(self, matches: List[Dict]):
        """Generate all reports"""
        try:
            # Get database statistics
            db_stats = self.db.get_statistics()
            
            # Generate comprehensive report
            html_report = self.reporter.generate_full_report(
                self.products_by_store,
                matches,
                db_stats
            )
            
            logger.info(f"Reports generated successfully")
            logger.info(f"HTML Report: {html_report}")
            
            # Export to CSV
            self.db.export_to_csv()
            logger.info("Data exported to CSV files")
            
        except Exception as e:
            logger.error(f"Error generating reports: {e}")

if __name__ == "__main__":
    orchestrator = MasterOrchestrator()
    orchestrator.run_complete_pipeline()
