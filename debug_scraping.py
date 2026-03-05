"""
Debug what's actually happening with the scraping
"""
from scrapers.base_scraper import BaseScraper
from config import SUPERMARKETS
import time

def debug_website_structure(supermarket_key):
    """Debug what we can actually access on each website"""
    config = SUPERMARKETS[supermarket_key]
    scraper = BaseScraper(config)

    try:
        print(f"\n🔍 DEBUGGING {config['name']}")
        print("-" * 40)

        scraper.start_browser()
        scraper.driver.get(config['base_url'])
        time.sleep(3)

        print(f"Page title: {scraper.driver.title}")
        print(f"Current URL: {scraper.driver.current_url}")

        # Try to find any links with dairy-related terms
        dairy_terms = ['lacteos', 'lácteos', 'leche', 'dairy', 'yogur', 'queso']

        found_links = []
        for term in dairy_terms:
            try:
                elements = scraper.driver.find_elements('xpath', f"//a[contains(text(), '{term}')]")
                for elem in elements:
                    href = elem.get_attribute('href')
                    if href and href not in found_links:
                        found_links.append(href)
                        print(f"Found {term} link: {href}")
            except:
                pass

        # Check page source for dairy terms
        page_source = scraper.driver.page_source.lower()
        dairy_mentions = sum([page_source.count(term) for term in dairy_terms])
        print(f"Total dairy term mentions in page: {dairy_mentions}")

        # Check if we can find any product listings
        product_selectors = [
            ".product", ".item", ".card", "[data-product]",
            ".product-item", ".product-card", ".grid-item"
        ]

        for selector in product_selectors:
            try:
                elements = scraper.driver.find_elements('css selector', selector)
                if elements:
                    print(f"Found {len(elements)} elements with selector: {selector}")
                    break
            except:
                pass

        scraper.close_browser()

    except Exception as e:
        print(f"Error debugging {config['name']}: {e}")
        if scraper.driver:
            scraper.close_browser()

def main():
    print("🐛 DEBUGGING SUPERMARKET WEBSITE ACCESS")
    print("=" * 50)

    for supermarket_key in SUPERMARKETS.keys():
        debug_website_structure(supermarket_key)
        time.sleep(2)

if __name__ == "__main__":
    main()