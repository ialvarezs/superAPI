"""
More targeted approach - search specifically for dairy products on Tienda Inglesa
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


def search_for_dairy_products(driver):
    """Search for specific dairy products using search functionality"""
    print("🔍 Searching for specific dairy products...")

    # Navigate with stealth
    driver.get('https://www.google.com')
    time.sleep(2)
    driver.get('https://www.tiendainglesa.com.uy')
    time.sleep(5)

    # Common dairy products to search for
    search_terms = [
        'leche', 'yogur', 'queso', 'manteca', 'crema',
        'dulce de leche', 'conaprole', 'parmalat', 'calcar'
    ]

    all_products = []

    for term in search_terms:
        print(f"\n🔎 Searching for: '{term}'")

        try:
            # Navigate to search page
            search_url = f"https://www.tiendainglesa.com.uy/supermercado/buscar?texto={term}"
            driver.get(search_url)
            time.sleep(4)

            # Scroll to load more products
            for i in range(3):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)

            soup = BeautifulSoup(driver.page_source, 'html.parser')

            # Find product containers
            products = soup.select('[class*="product"]')
            print(f"  Found {len(products)} product elements")

            # Extract products from this search
            search_products = []
            for element in products[:15]:  # Limit per search
                product = extract_product_info(element)
                if product and product.get('name') and is_dairy_product(product['name']):
                    search_products.append(product)

            print(f"  ✅ Extracted {len(search_products)} dairy products")

            for product in search_products[:3]:  # Show sample
                print(f"    • {product['name'][:50]}... - ${product.get('price', 'N/A')}")

            all_products.extend(search_products)

            # Random delay between searches
            time.sleep(random.uniform(3, 6))

        except Exception as e:
            print(f"    ❌ Error searching for '{term}': {e}")
            continue

    return all_products


def extract_product_info(element):
    """Extract detailed product information"""
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
        # Extract name - more comprehensive approach
        name_elem = None

        # Try different approaches to find the product name
        name_selectors = [
            '.product-title', '.titulo', '.name', 'h1', 'h2', 'h3',
            '[class*="title"]', '[class*="name"]', '[data-name]'
        ]

        for selector in name_selectors:
            elem = element.select_one(selector)
            if elem and elem.get_text().strip():
                name_elem = elem
                break

        if name_elem:
            full_text = name_elem.get_text().strip()
            # Clean up the name by removing extra whitespace and price info
            clean_name = re.sub(r'\s+', ' ', full_text)
            clean_name = re.sub(r'Antes\s*\$.*', '', clean_name)  # Remove "Antes $" price
            clean_name = re.sub(r'\$\s*[\d.,]+.*', '', clean_name)  # Remove trailing prices
            product['name'] = clean_name.strip()

        # Extract price - look for price elements
        price_elem = None
        price_selectors = [
            '.price', '.precio', '[class*="price"]', '[data-price]',
            '.amount', '.valor', '.cost'
        ]

        for selector in price_selectors:
            elem = element.select_one(selector)
            if elem and elem.get_text().strip():
                price_text = elem.get_text().strip()
                product['original_price'] = price_text

                # Extract numeric price
                # Look for patterns like $123, 123.45, etc.
                price_matches = re.findall(r'[\d.,]+', price_text)
                if price_matches:
                    # Take the last number (often the final price after discounts)
                    price_str = price_matches[-1].replace(',', '.')
                    try:
                        product['price'] = float(price_str)
                        break
                    except:
                        pass

        # If no price element found, try to extract from the main text
        if not product['price'] and product['name']:
            price_matches = re.findall(r'\$\s*([\d.,]+)', product['name'])
            if price_matches:
                try:
                    product['price'] = float(price_matches[-1].replace(',', '.'))
                    # Clean the price from the name
                    product['name'] = re.sub(r'\$\s*[\d.,]+.*', '', product['name']).strip()
                except:
                    pass

        # Extract image URL
        img = element.select_one('img')
        if img:
            src = img.get('src') or img.get('data-src') or img.get('data-lazy')
            if src and 'http' in src:
                product['image_url'] = src

        # Extract product URL
        link = element.select_one('a')
        if link and link.get('href'):
            href = link['href']
            if href.startswith('http'):
                product['url'] = href
            elif href.startswith('/'):
                product['url'] = f"https://www.tiendainglesa.com.uy{href}"

        # Extract brand from name
        if product['name']:
            # Common Uruguayan brands
            brands = {
                'conaprole': 'Conaprole',
                'parmalat': 'Parmalat',
                'calcar': 'Calcar',
                'sancor': 'Sancor',
                'talar': 'Talar',
                'serenisima': 'La Serenísima',
                'claldy': 'Claldy',
                'milky': 'Milky'
            }

            name_lower = product['name'].lower()
            for brand_key, brand_name in brands.items():
                if brand_key in name_lower:
                    product['brand'] = brand_name
                    break

            # If no brand found, try first word
            if not product['brand']:
                words = product['name'].split()
                if words and len(words[0]) > 2:
                    product['brand'] = words[0].title()

        return product

    except Exception as e:
        print(f"      Error extracting product: {e}")
        return None


def is_dairy_product(name):
    """Enhanced dairy product detection"""
    if not name:
        return False

    name_lower = name.lower()

    # Core dairy products
    dairy_keywords = [
        'leche', 'milk', 'yogur', 'yogurt', 'queso', 'cheese',
        'manteca', 'butter', 'crema', 'cream', 'ricotta',
        'mozzarella', 'cheddar', 'parmesano', 'gouda',
        'dulce de leche', 'natilla', 'flan'
    ]

    # Exclude non-dairy items that might have dairy words
    exclusions = [
        'empanada', 'alfajor', 'chocolate', 'helado', 'torta',
        'cookie', 'galleta', 'bizcocho', 'pan'
    ]

    # Check for dairy keywords
    has_dairy = any(keyword in name_lower for keyword in dairy_keywords)

    # Check for exclusions
    has_exclusion = any(exclusion in name_lower for exclusion in exclusions)

    return has_dairy and not has_exclusion


def main():
    print("🎯 TARGETED TIENDA INGLESA DAIRY SCRAPER")
    print("=" * 50)

    driver = None
    all_products = []

    try:
        driver = create_stealth_browser()

        # Search for dairy products
        products = search_for_dairy_products(driver)

        # Remove duplicates based on name similarity
        unique_products = []
        seen_names = set()

        for product in products:
            if not product or not product.get('name'):
                continue

            # Create a normalized name for comparison
            norm_name = re.sub(r'[^\w\s]', '', product['name'].lower())
            norm_name = re.sub(r'\s+', ' ', norm_name).strip()

            if norm_name and norm_name not in seen_names:
                unique_products.append(product)
                seen_names.add(norm_name)

        print(f"\n📊 FINAL RESULTS")
        print(f"-" * 25)
        print(f"Total products found: {len(products)}")
        print(f"Unique dairy products: {len(unique_products)}")

        # Save results
        with open('data/tienda_inglesa_dairy_targeted.json', 'w', encoding='utf-8') as f:
            json.dump(unique_products, f, ensure_ascii=False, indent=2)

        if unique_products:
            import pandas as pd
            df = pd.DataFrame(unique_products)
            df.to_csv('data/tienda_inglesa_dairy_targeted.csv', index=False, encoding='utf-8')

        print(f"✅ Results saved to:")
        print(f"  • data/tienda_inglesa_dairy_targeted.json ({len(unique_products)} products)")
        print(f"  • data/tienda_inglesa_dairy_targeted.csv")

        # Show detailed results
        if unique_products:
            print(f"\n🥛 FOUND DAIRY PRODUCTS:")
            for i, product in enumerate(unique_products, 1):
                print(f"{i:2d}. {product['name']}")
                print(f"     Price: ${product.get('price', 'N/A')} | Brand: {product.get('brand', 'N/A')}")
                if product.get('url'):
                    print(f"     URL: {product['url']}")
                print()

        return unique_products

    except Exception as e:
        print(f"❌ Error in main scraping: {e}")
        import traceback
        traceback.print_exc()
        return []

    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    products = main()
    print(f"\n🎉 Targeted scraping completed! Found {len(products)} real dairy products from Tienda Inglesa")