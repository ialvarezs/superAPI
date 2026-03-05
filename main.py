"""
Main script to run the supermarket scraping POC
"""
import asyncio
import concurrent.futures
from config import SUPERMARKETS
from scrapers.base_scraper import BaseScraper
from product_matcher import ProductMatcher
import os


def scrape_supermarket(supermarket_key):
    """Scrape a single supermarket"""
    config = SUPERMARKETS[supermarket_key]
    scraper = BaseScraper(config)

    try:
        products = scraper.run_scraping()
        return supermarket_key, products
    except Exception as e:
        print(f"Error scraping {config['name']}: {e}")
        return supermarket_key, []


def main():
    """Main function to coordinate scraping and matching"""
    print("🛒 Starting Supermarket Scraping POC - Lacteos Category")
    print("=" * 60)

    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    os.makedirs('results', exist_ok=True)

    # Scrape all supermarkets in parallel
    all_products = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(scrape_supermarket, key): key
            for key in SUPERMARKETS.keys()
        }

        for future in concurrent.futures.as_completed(futures):
            supermarket_key, products = future.result()
            all_products[supermarket_key] = products
            print(f"✅ Completed scraping {SUPERMARKETS[supermarket_key]['name']}: {len(products)} products")

    # Print summary
    print("\n📊 SCRAPING SUMMARY")
    print("-" * 30)
    total_products = 0
    for key, products in all_products.items():
        name = SUPERMARKETS[key]['name']
        count = len(products)
        total_products += count
        print(f"{name}: {count} products")

    print(f"\nTotal products scraped: {total_products}")

    # Match products across supermarkets
    if total_products > 0:
        print("\n🔍 Starting product matching...")
        matcher = ProductMatcher()

        # Convert to list format for matcher
        all_products_list = []
        for products in all_products.values():
            all_products_list.extend(products)

        matches = matcher.find_matches(all_products_list)

        print(f"Found {len(matches)} product matches across supermarkets")

        # Save matching results
        matcher.save_matches(matches, 'results/product_matches.json')
        matcher.create_comparison_report(matches, 'results/price_comparison.csv')

        print("✅ Results saved in 'results/' directory")
    else:
        print("❌ No products were scraped. Check website accessibility and selectors.")


if __name__ == "__main__":
    main()