"""
Production runner for scraping all Uruguayan supermarkets
Coordinates Tienda Inglesa, Disco, and Devoto scrapers
"""
import time
import json
from datetime import datetime
from typing import List, Dict
import pandas as pd

from tienda_inglesa_production_scraper import TiendaInglesaScraper
from scrapers.base_scraper import BaseScraper
from config import SUPERMARKETS
from product_matcher import ProductMatcher
from database import DatabaseManager


class ProductionScraperRunner:
    """Coordinates scraping across all supermarkets"""
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.all_products = []
        self.scraping_stats = {
            'start_time': None,
            'end_time': None,
            'supermarkets': {},
            'total_products': 0,
            'total_matched': 0
        }
    
    def scrape_tienda_inglesa(self) -> List[Dict]:
        """Scrape Tienda Inglesa"""
        print("\n" + "="*80)
        print("🏪 SCRAPING: TIENDA INGLESA")
        print("="*80)
        
        try:
            scraper = TiendaInglesaScraper(
                headless=self.headless,
                max_products=50  # Reasonable limit
            )
            
            products = scraper.scrape_with_strategy(strategy='hybrid')
            scraper.save_results('tienda_inglesa_production')
            
            self.scraping_stats['supermarkets']['Tienda Inglesa'] = {
                'products': len(products),
                'status': 'success',
                'error': None
            }
            
            return products
            
        except Exception as e:
            print(f"❌ Error scraping Tienda Inglesa: {e}")
            self.scraping_stats['supermarkets']['Tienda Inglesa'] = {
                'products': 0,
                'status': 'error',
                'error': str(e)
            }
            return []
    
    def scrape_disco(self) -> List[Dict]:
        """Scrape Disco"""
        print("\n" + "="*80)
        print("🏪 SCRAPING: DISCO")
        print("="*80)
        
        try:
            scraper = BaseScraper(SUPERMARKETS['disco'])
            products = scraper.run_scraping()
            
            self.scraping_stats['supermarkets']['Disco'] = {
                'products': len(products),
                'status': 'success',
                'error': None
            }
            
            return products
            
        except Exception as e:
            print(f"❌ Error scraping Disco: {e}")
            self.scraping_stats['supermarkets']['Disco'] = {
                'products': 0,
                'status': 'error',
                'error': str(e)
            }
            return []
    
    def scrape_devoto(self) -> List[Dict]:
        """Scrape Devoto"""
        print("\n" + "="*80)
        print("🏪 SCRAPING: DEVOTO")
        print("="*80)
        
        try:
            scraper = BaseScraper(SUPERMARKETS['devoto'])
            products = scraper.run_scraping()
            
            self.scraping_stats['supermarkets']['Devoto'] = {
                'products': len(products),
                'status': 'success',
                'error': None
            }
            
            return products
            
        except Exception as e:
            print(f"❌ Error scraping Devoto: {e}")
            self.scraping_stats['supermarkets']['Devoto'] = {
                'products': 0,
                'status': 'error',
                'error': str(e)
            }
            return []
    
    def run_full_scraping(self, supermarkets: List[str] = None) -> List[Dict]:
        """
        Run scraping for all or selected supermarkets
        
        Args:
            supermarkets: List of supermarket names to scrape.
                         If None, scrapes all. Options: ['Tienda Inglesa', 'Disco', 'Devoto']
        """
        self.scraping_stats['start_time'] = datetime.now().isoformat()
        
        print("\n" + "🚀"*40)
        print("PRODUCTION SUPERMARKET SCRAPER")
        print("Uruguay Dairy Products Collection")
        print("🚀"*40)
        
        # Determine which supermarkets to scrape
        if supermarkets is None:
            supermarkets = ['Tienda Inglesa', 'Disco', 'Devoto']
        
        # Scrape each supermarket
        for supermarket in supermarkets:
            try:
                if supermarket == 'Tienda Inglesa':
                    products = self.scrape_tienda_inglesa()
                    self.all_products.extend(products)
                
                elif supermarket == 'Disco':
                    products = self.scrape_disco()
                    self.all_products.extend(products)
                
                elif supermarket == 'Devoto':
                    products = self.scrape_devoto()
                    self.all_products.extend(products)
                
                # Delay between supermarkets
                if supermarket != supermarkets[-1]:
                    print("\n⏳ Waiting before next supermarket...")
                    time.sleep(5)
            
            except Exception as e:
                print(f"❌ Fatal error with {supermarket}: {e}")
                continue
        
        self.scraping_stats['end_time'] = datetime.now().isoformat()
        self.scraping_stats['total_products'] = len(self.all_products)
        
        # Summary
        self.print_summary()
        
        return self.all_products
    
    def match_products(self) -> Dict:
        """Match products across supermarkets"""
        print("\n" + "="*80)
        print("🔗 MATCHING PRODUCTS ACROSS SUPERMARKETS")
        print("="*80)
        
        if len(self.all_products) < 2:
            print("⚠️  Not enough products to match (need at least 2)")
            return {}
        
        try:
            matcher = ProductMatcher()
            matches = matcher.find_matches(self.all_products)
            
            self.scraping_stats['total_matched'] = len(matches)
            
            print(f"\n✅ Found {len(matches)} product matches across supermarkets")
            
            # Save matches
            with open('results/production_matches.json', 'w', encoding='utf-8') as f:
                json.dump(matches, f, ensure_ascii=False, indent=2)
            
            # Create comparison CSV
            if matches:
                comparison_data = []
                for match in matches:
                    for i in range(len(match['products']) - 1):
                        for j in range(i + 1, len(match['products'])):
                            p1 = match['products'][i]
                            p2 = match['products'][j]
                            
                            if p1.get('price') and p2.get('price'):
                                diff = abs(p1['price'] - p2['price'])
                                pct = (diff / min(p1['price'], p2['price'])) * 100
                                
                                comparison_data.append({
                                    'Product': match['matched_name'],
                                    'Store_1': p1['supermarket'],
                                    'Price_1': p1['price'],
                                    'Store_2': p2['supermarket'],
                                    'Price_2': p2['price'],
                                    'Difference': diff,
                                    'Percentage': f"{pct:.1f}%",
                                    'Cheaper_Store': p1['supermarket'] if p1['price'] < p2['price'] else p2['supermarket']
                                })
                
                if comparison_data:
                    df = pd.DataFrame(comparison_data)
                    df = df.sort_values('Percentage', ascending=False)
                    df.to_csv('results/production_price_comparison.csv', index=False)
                    
                    print(f"💾 Price comparison saved to results/production_price_comparison.csv")
                    
                    # Show top 5 deals
                    print("\n💰 TOP 5 PRICE DIFFERENCES:")
                    print("-" * 80)
                    for idx, row in df.head(5).iterrows():
                        print(f"• {row['Product'][:50]}")
                        print(f"  {row['Store_1']}: ${row['Price_1']:.0f} vs {row['Store_2']}: ${row['Price_2']:.0f}")
                        print(f"  💵 Save ${row['Difference']:.0f} ({row['Percentage']}) at {row['Cheaper_Store']}")
                        print()
            
            return matches
            
        except Exception as e:
            print(f"❌ Error matching products: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def save_to_database(self, db_path: str = 'data/production.db'):
        """Save all products to database"""
        print("\n" + "="*80)
        print("💾 SAVING TO DATABASE")
        print("="*80)
        
        try:
            db = DatabaseManager(db_path)
            
            for product in self.all_products:
                db.insert_product(product)
            
            print(f"✅ Saved {len(self.all_products)} products to {db_path}")
            
        except Exception as e:
            print(f"❌ Error saving to database: {e}")
    
    def print_summary(self):
        """Print scraping summary"""
        print("\n" + "="*80)
        print("📊 SCRAPING SUMMARY")
        print("="*80)
        
        print(f"\n⏱️  Duration: {self.scraping_stats['start_time']} to {self.scraping_stats['end_time']}")
        print(f"\n📦 Products by Supermarket:")
        
        for supermarket, stats in self.scraping_stats['supermarkets'].items():
            status_icon = "✅" if stats['status'] == 'success' else "❌"
            print(f"   {status_icon} {supermarket}: {stats['products']} products")
            if stats['error']:
                print(f"      Error: {stats['error']}")
        
        print(f"\n📊 Total Products: {self.scraping_stats['total_products']}")
        
        # Product statistics
        products_with_prices = sum(1 for p in self.all_products if p.get('price'))
        products_with_brands = sum(1 for p in self.all_products if p.get('brand'))
        products_with_images = sum(1 for p in self.all_products if p.get('image_url'))
        
        print(f"\n📈 Data Quality:")
        print(f"   • Products with prices: {products_with_prices} ({products_with_prices/len(self.all_products)*100:.1f}%)")
        print(f"   • Products with brands: {products_with_brands} ({products_with_brands/len(self.all_products)*100:.1f}%)")
        print(f"   • Products with images: {products_with_images} ({products_with_images/len(self.all_products)*100:.1f}%)")
        
        # Save summary
        with open('results/production_summary.json', 'w', encoding='utf-8') as f:
            json.dump(self.scraping_stats, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Summary saved to results/production_summary.json")
    
    def save_all_products(self):
        """Save all products to JSON and CSV"""
        if not self.all_products:
            return
        
        # JSON
        with open('data/production_all_products.json', 'w', encoding='utf-8') as f:
            json.dump(self.all_products, f, ensure_ascii=False, indent=2)
        
        # CSV
        df = pd.DataFrame(self.all_products)
        df.to_csv('data/production_all_products.csv', index=False, encoding='utf-8')
        
        print(f"\n💾 All products saved:")
        print(f"   • data/production_all_products.json")
        print(f"   • data/production_all_products.csv")


def main():
    """Main entry point"""
    print("🛒 URUGUAY SUPERMARKET SCRAPER - PRODUCTION MODE\n")
    
    # Configuration
    HEADLESS = False  # Set to True for production/server
    SUPERMARKETS_TO_SCRAPE = ['Tienda Inglesa']  # Can add 'Disco', 'Devoto'
    
    # Create runner
    runner = ProductionScraperRunner(headless=HEADLESS)
    
    # Run scraping
    products = runner.run_full_scraping(supermarkets=SUPERMARKETS_TO_SCRAPE)
    
    # Save all products
    runner.save_all_products()
    
    # Match products if multiple supermarkets
    if len(SUPERMARKETS_TO_SCRAPE) > 1:
        runner.match_products()
    
    # Save to database
    runner.save_to_database()
    
    print("\n" + "🎉"*40)
    print("SCRAPING COMPLETE!")
    print("🎉"*40)
    print(f"\n✅ Successfully scraped {len(products)} dairy products")
    print(f"📂 Check the data/ and results/ directories for output files")
    
    return products


if __name__ == "__main__":
    main()
