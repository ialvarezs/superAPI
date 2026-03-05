"""
Main runner script with database integration
"""
import os
import sys
from datetime import datetime
from config import SUPERMARKETS
from scrapers.base_scraper import BaseScraper
from product_matcher import ProductMatcher
from database import ProductDatabase
from analyzer import SupermarketAnalyzer
import concurrent.futures


def scrape_supermarket_to_db(supermarket_key: str, db: ProductDatabase):
    """Scrape a supermarket and save directly to database"""
    config = SUPERMARKETS[supermarket_key]
    scraper = BaseScraper(config)

    try:
        print(f"🔍 Starting scraping for {config['name']}...")
        products = scraper.run_scraping()

        if products:
            db.save_products(products, config['name'])
            return supermarket_key, len(products)
        else:
            print(f"❌ No products found for {config['name']}")
            return supermarket_key, 0

    except Exception as e:
        print(f"❌ Error scraping {config['name']}: {e}")
        return supermarket_key, 0


def main():
    """Enhanced main function with database integration"""
    print("🛒 SUPERMARKET SCRAPING POC - LACTEOS CATEGORY")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Setup
    os.makedirs('data', exist_ok=True)
    os.makedirs('results', exist_ok=True)

    # Initialize database
    db = ProductDatabase()

    # Scrape all supermarkets
    print("🕷️ SCRAPING PHASE")
    print("-" * 20)

    results = {}
    total_scraped = 0

    # Sequential scraping (to avoid being blocked)
    for supermarket_key in SUPERMARKETS.keys():
        name, count = scrape_supermarket_to_db(supermarket_key, db)
        results[name] = count
        total_scraped += count
        print(f"✅ {SUPERMARKETS[supermarket_key]['name']}: {count} products")

        # Small delay between supermarkets
        import time
        time.sleep(2)

    print(f"\n📊 SCRAPING SUMMARY: {total_scraped} total products")

    if total_scraped == 0:
        print("❌ No products were scraped. Check website accessibility.")
        return

    # Product matching phase
    print(f"\n🔍 PRODUCT MATCHING PHASE")
    print("-" * 25)

    # Get all products from database
    all_products = db.get_products()
    print(f"Loaded {len(all_products)} products from database")

    # Find matches
    matcher = ProductMatcher()
    matches = matcher.find_matches(all_products)

    if matches:
        # Save matches to database
        db.save_matches(matches)

        # Also save to JSON for backup
        matcher.save_matches(matches, 'results/product_matches.json')

        print(f"✅ Found and saved {len(matches)} product matches")
    else:
        print("❌ No product matches found")

    # Analysis phase
    print(f"\n📈 ANALYSIS PHASE")
    print("-" * 15)

    analyzer = SupermarketAnalyzer()
    report = analyzer.generate_report('results/analysis_report.json')

    # Export data
    db.export_to_csv('results')
    analyzer.export_deals_csv('results/best_deals.csv')

    try:
        analyzer.create_visualizations('results/plots')
    except Exception as e:
        print(f"Could not create visualizations: {e}")

    print(f"\n🎉 POC COMPLETED!")
    print("-" * 15)
    print(f"Results saved in 'results/' directory:")
    print(f"  • Database: data/products.db")
    print(f"  • Analysis report: results/analysis_report.json")
    print(f"  • Best deals: results/best_deals.csv")
    print(f"  • All data: results/all_products.csv, results/product_matches.csv")

    # Print final statistics
    stats = db.get_statistics()
    print(f"\n📊 FINAL STATISTICS:")
    print(f"  • Total products: {stats['total_products']}")
    print(f"  • Products with barcodes: {stats['products_with_barcodes']}")
    print(f"  • Total matches: {stats['total_matches']}")

    if stats['total_matches'] > 0:
        print("\n✅ Success! Product matching across supermarkets is working.")
        if stats['products_with_barcodes'] > 0:
            print(f"📱 {stats['products_with_barcodes']} products have barcodes for reliable matching.")
    else:
        print("\n⚠️  No matches found. This could mean:")
        print("   • Different product catalogs between stores")
        print("   • Need to adjust similarity thresholds")
        print("   • Limited product data extracted")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️ Scraping interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()