"""
Focused scraper to extract real lacteos products from Tienda Inglesa
"""
import time
import random
import json
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup


def create_stealth_browser():
    """Create a stealthy Chrome browser"""
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-automation')

    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    options.add_argument(f'--user-agent={user_agent}')
    options.add_argument('--window-size=1400,900')
    options.add_argument('--lang=es-UY')

    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.binary_location = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    return driver


def find_lacteos_categories(driver):
    """Find lacteos categories on Tienda Inglesa"""
    print("🔍 Searching for lacteos categories...")

    try:
        # Navigate to main site
        driver.get('https://www.google.com')
        time.sleep(2)

        driver.get('https://www.tiendainglesa.com.uy')
        time.sleep(5)

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Look for category navigation - common patterns
        category_urls = set()

        # Strategy 1: Look for direct lacteos links
        dairy_terms = ['lacteos', 'lácteos', 'leche', 'yogur', 'queso', 'manteca', 'crema']

        all_links = soup.find_all('a', href=True)
        for link in all_links:
            href = link.get('href', '')
            text = link.get_text().lower().strip()

            # Check if link contains dairy terms
            if any(term in text or term in href.lower() for term in dairy_terms):
                full_url = href if href.startswith('http') else f"https://www.tiendainglesa.com.uy{href}"
                category_urls.add(full_url)
                print(f"  Found potential category: {text[:50]} → {full_url}")

        # Strategy 2: Look for main category pages that might contain dairy
        category_patterns = [
            r'/categoria[s]?[/-]',
            r'/section[s]?[/-]',
            r'/departamento[s]?[/-]',
            r'/supermercado[/-].*categoria',
            r'/categoria.*alimentos',
            r'/alimentos',
            r'/frescos'
        ]

        for link in all_links:
            href = link.get('href', '')
            if any(re.search(pattern, href, re.I) for pattern in category_patterns):
                full_url = href if href.startswith('http') else f"https://www.tiendainglesa.com.uy{href}"
                category_urls.add(full_url)

        # Strategy 3: Try search for "leche" (most common dairy product)
        try:
            search_url = "https://www.tiendainglesa.com.uy/supermercado/buscar?texto=leche"
            category_urls.add(search_url)
            print(f"  Added search URL: {search_url}")
        except:
            pass

        return list(category_urls)[:10]  # Limit to first 10 URLs

    except Exception as e:
        print(f"❌ Error finding categories: {e}")
        return []


def scrape_products_from_url(driver, url):
    """Scrape products from a specific URL"""
    print(f"\n🛒 Scraping products from: {url}")

    try:
        driver.get(url)
        time.sleep(5)

        # Scroll down to load more products (many sites use lazy loading)
        for i in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Find product containers - try different selectors
        product_selectors = [
            '.product-item', '.product-card', '.product',
            '[class*="product"]', '[data-product]',
            '.item-product', '.card-product'
        ]

        products = []

        for selector in product_selectors:
            elements = soup.select(selector)
            if elements:
                print(f"  Found {len(elements)} elements with selector: {selector}")

                for element in elements[:20]:  # Limit to first 20 per selector
                    product = extract_product_info(element, driver.current_url)
                    if product and product.get('name') and 'lacteo' in url.lower() or is_dairy_product(product.get('name', '')):
                        products.append(product)
                        print(f"    ✓ {product['name'][:50]}... - ${product.get('price', 'N/A')}")

                if products:  # If we found products with this selector, use it
                    break

        return products

    except Exception as e:
        print(f"    ❌ Error scraping {url}: {e}")
        return []


def extract_product_info(element, base_url):
    """Extract product information from a product element"""
    product = {
        'supermarket': 'Tienda Inglesa',
        'name': None,
        'price': None,
        'original_price': None,
        'brand': None,
        'barcode': None,
        'image_url': None,
        'url': None,
        'description': None
    }

    try:
        # Extract name - try multiple selectors
        name_selectors = [
            '.product-title', '.title', '.name', '.product-name',
            'h1', 'h2', 'h3', 'h4', '.heading',
            '[class*="title"]', '[class*="name"]'
        ]

        for selector in name_selectors:
            name_elem = element.select_one(selector)
            if name_elem and name_elem.get_text().strip():
                product['name'] = name_elem.get_text().strip()
                break

        # Extract price
        price_selectors = [
            '.price', '.precio', '.cost', '[class*="price"]',
            '.amount', '.value', '[data-price]'
        ]

        for selector in price_selectors:
            price_elem = element.select_one(selector)
            if price_elem and price_elem.get_text().strip():
                price_text = price_elem.get_text().strip()
                product['original_price'] = price_text

                # Extract numeric price
                price_match = re.search(r'[\d.,]+', price_text.replace('$', '').replace(',', '.'))
                if price_match:
                    try:
                        product['price'] = float(price_match.group().replace(',', '.'))
                    except:
                        pass
                break

        # Extract image
        img = element.select_one('img')
        if img:
            src = img.get('src') or img.get('data-src') or img.get('data-lazy')
            if src:
                if src.startswith('http'):
                    product['image_url'] = src
                elif src.startswith('/'):
                    product['image_url'] = f"https://www.tiendainglesa.com.uy{src}"

        # Extract product URL
        link = element.select_one('a')
        if link:
            href = link.get('href')
            if href:
                if href.startswith('http'):
                    product['url'] = href
                elif href.startswith('/'):
                    product['url'] = f"https://www.tiendainglesa.com.uy{href}"

        # Try to extract brand from name
        if product['name']:
            name_words = product['name'].split()
            if name_words:
                # Common Uruguayan dairy brands
                brands = ['conaprole', 'parmalat', 'calcar', 'sancor', 'talar', 'claldy', 'serenisima']
                for word in name_words:
                    if word.lower() in brands:
                        product['brand'] = word.title()
                        break

                if not product['brand'] and len(name_words) > 0:
                    # First word might be the brand
                    product['brand'] = name_words[0].title()

        return product

    except Exception as e:
        print(f"      Error extracting product info: {e}")
        return product


def is_dairy_product(name):
    """Check if a product name suggests it's a dairy product"""
    if not name:
        return False

    name_lower = name.lower()
    dairy_keywords = [
        'leche', 'milk', 'yogur', 'yogurt', 'queso', 'cheese',
        'manteca', 'butter', 'crema', 'cream', 'dulce de leche',
        'ricotta', 'mozzarella', 'cheddar', 'parmesano'
    ]

    return any(keyword in name_lower for keyword in dairy_keywords)


def main():
    print("🥛 TIENDA INGLESA LACTEOS SCRAPER")
    print("=" * 50)

    driver = None
    all_products = []

    try:
        driver = create_stealth_browser()

        # Find lacteos categories
        category_urls = find_lacteos_categories(driver)
        print(f"\nFound {len(category_urls)} potential category URLs")

        # Scrape products from each category
        for i, url in enumerate(category_urls, 1):
            print(f"\n[{i}/{len(category_urls)}] Processing: {url}")
            products = scrape_products_from_url(driver, url)
            all_products.extend(products)

            # Add delay between requests
            time.sleep(random.uniform(2, 5))

        # Remove duplicates based on name
        unique_products = []
        seen_names = set()

        for product in all_products:
            name = product.get('name', '').lower().strip()
            if name and name not in seen_names:
                unique_products.append(product)
                seen_names.add(name)

        print(f"\n📊 SCRAPING RESULTS")
        print(f"-" * 25)
        print(f"Total products found: {len(all_products)}")
        print(f"Unique products: {len(unique_products)}")

        # Save results
        with open('data/tienda_inglesa_lacteos_real.json', 'w', encoding='utf-8') as f:
            json.dump(unique_products, f, ensure_ascii=False, indent=2)

        # Save to CSV as well
        if unique_products:
            import pandas as pd
            df = pd.DataFrame(unique_products)
            df.to_csv('data/tienda_inglesa_lacteos_real.csv', index=False, encoding='utf-8')

        print(f"✅ Results saved to:")
        print(f"  • data/tienda_inglesa_lacteos_real.json")
        print(f"  • data/tienda_inglesa_lacteos_real.csv")

        # Show sample products
        if unique_products:
            print(f"\n🛒 SAMPLE PRODUCTS:")
            for product in unique_products[:5]:
                print(f"  • {product['name'][:60]}...")
                print(f"    Price: ${product.get('price', 'N/A')} | Brand: {product.get('brand', 'N/A')}")

        return unique_products

    except Exception as e:
        print(f"❌ Error in main scraping: {e}")
        return []

    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    products = main()
    print(f"\n🎉 Scraping completed! Found {len(products)} dairy products from Tienda Inglesa")