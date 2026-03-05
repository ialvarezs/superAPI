"""
Test broader categories to get more products from supermarkets
"""
import time
import random
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup


def create_stealth_browser():
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


def analyze_tienda_inglesa_categories():
    """Analyze what categories are actually available"""
    print("🔍 ANALYZING TIENDA INGLESA CATEGORIES")
    print("=" * 50)

    driver = None
    try:
        driver = create_stealth_browser()

        # Navigate to site
        driver.get('https://www.google.com')
        time.sleep(2)
        driver.get('https://www.tiendainglesa.com.uy')
        time.sleep(5)

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Look for category links in navigation
        print("🗂️ FOUND CATEGORIES:")

        # Find all links that look like categories
        all_links = soup.find_all('a', href=True)
        categories = set()

        for link in all_links:
            href = link.get('href', '')
            text = link.get_text().strip()

            # Look for category URLs
            if '/categoria/' in href or '/category/' in href:
                categories.add((text, href))

            # Look for section URLs
            if '/seccion/' in href or '/section/' in href:
                categories.add((text, href))

        # Sort and display categories
        sorted_categories = sorted(categories)

        for i, (text, href) in enumerate(sorted_categories[:20]):
            full_url = href if href.startswith('http') else f"https://www.tiendainglesa.com.uy{href}"
            print(f"  {i+1:2d}. '{text[:30]:30}' → {full_url}")

        # Test some promising categories
        test_categories = [
            ('almacen', 'https://www.tiendainglesa.com.uy/supermercado/categoria/almacen/78'),
            ('bebidas', 'https://www.tiendainglesa.com.uy/supermercado/categoria/bebidas/175'),
            ('frescos', 'https://www.tiendainglesa.com.uy/supermercado/categoria/frescos/206'),
            ('congelados', 'https://www.tiendainglesa.com.uy/supermercado/categoria/congelados/181')
        ]

        category_results = {}

        for category_name, category_url in test_categories:
            print(f"\n🛒 TESTING CATEGORY: {category_name.upper()}")
            print(f"   URL: {category_url}")

            try:
                driver.get(category_url)
                time.sleep(4)

                # Scroll to load products
                for i in range(2):
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)

                soup = BeautifulSoup(driver.page_source, 'html.parser')
                product_containers = soup.select('.card-product-container')

                print(f"   Found {len(product_containers)} products in {category_name}")

                # Extract sample products
                sample_products = []
                for container in product_containers[:10]:  # First 10
                    try:
                        name_elem = container.select_one('.card-product-name')
                        price_elem = container.select_one('.ProductPrice')

                        if name_elem and price_elem:
                            name = name_elem.get_text().strip()
                            price = price_elem.get_text().strip()
                            sample_products.append({'name': name, 'price': price})

                    except Exception as e:
                        continue

                category_results[category_name] = {
                    'url': category_url,
                    'total_products': len(product_containers),
                    'sample_products': sample_products
                }

                # Show sample products
                print(f"   Sample products:")
                for product in sample_products[:5]:
                    print(f"     • {product['name'][:50]}... - {product['price']}")

                time.sleep(random.uniform(3, 5))

            except Exception as e:
                print(f"   ❌ Error testing {category_name}: {e}")
                category_results[category_name] = {'error': str(e)}

        # Save results
        with open('results/tienda_inglesa_category_analysis.json', 'w', encoding='utf-8') as f:
            json.dump({
                'all_categories': sorted_categories,
                'category_tests': category_results
            }, f, ensure_ascii=False, indent=2)

        print(f"\n📊 CATEGORY ANALYSIS SUMMARY:")
        print(f"   Found {len(sorted_categories)} total categories")

        for category_name, results in category_results.items():
            if 'total_products' in results:
                print(f"   {category_name}: {results['total_products']} products")

        return category_results

    except Exception as e:
        print(f"❌ Error: {e}")
        return {}

    finally:
        if driver:
            driver.quit()


def test_broad_product_extraction():
    """Test extracting products from the most promising category"""
    print(f"\n🚀 BROAD PRODUCT EXTRACTION TEST")
    print("=" * 40)

    driver = None
    try:
        driver = create_stealth_browser()

        # Navigate to site
        driver.get('https://www.google.com')
        time.sleep(2)
        driver.get('https://www.tiendainglesa.com.uy')
        time.sleep(5)

        # Test the 'almacen' category (grocery staples)
        almacen_url = "https://www.tiendainglesa.com.uy/supermercado/categoria/almacen/78"

        print(f"🛒 Extracting products from ALMACEN category...")
        driver.get(almacen_url)
        time.sleep(5)

        # Scroll multiple times to load more products
        for i in range(5):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        product_containers = soup.select('.card-product-container')

        print(f"Found {len(product_containers)} total product containers")

        # Extract detailed product information
        products = []
        for i, container in enumerate(product_containers[:50]):  # Limit to first 50
            try:
                product = {
                    'supermarket': 'Tienda Inglesa',
                    'category': 'almacen',
                    'name': None,
                    'price': None,
                    'original_price': None,
                    'brand': None,
                    'image_url': None,
                    'url': None
                }

                # Extract name
                name_elem = container.select_one('.card-product-name')
                if name_elem:
                    product['name'] = name_elem.get_text().strip()

                # Extract price
                price_elem = container.select_one('.ProductPrice')
                if price_elem:
                    price_text = price_elem.get_text().strip()
                    product['original_price'] = price_text

                    # Extract numeric price
                    import re
                    price_match = re.search(r'[\d.,]+', price_text.replace('$', '').strip())
                    if price_match:
                        try:
                            product['price'] = float(price_match.group().replace(',', '.'))
                        except:
                            pass

                # Extract image
                img_elem = container.select_one('.card-product-img')
                if img_elem:
                    src = img_elem.get('src') or img_elem.get('data-src')
                    if src and 'http' in src:
                        product['image_url'] = src

                # Extract URL
                link_elem = container.select_one('a[href*="producto"]')
                if link_elem:
                    href = link_elem.get('href')
                    if href:
                        if href.startswith('http'):
                            product['url'] = href
                        else:
                            product['url'] = f"https://www.tiendainglesa.com.uy{href}"

                # Extract brand (first word of name)
                if product['name']:
                    words = product['name'].split()
                    if words and words[0][0].isupper():
                        product['brand'] = words[0]

                if product['name'] and product['price']:
                    products.append(product)
                    if i < 10:  # Show first 10
                        print(f"  {i+1:2d}. {product['name'][:50]}... - ${product['price']}")

            except Exception as e:
                continue

        print(f"\n✅ Extracted {len(products)} complete products from Almacen category")

        # Save results
        with open('data/tienda_inglesa_almacen_products.json', 'w', encoding='utf-8') as f:
            json.dump(products, f, ensure_ascii=False, indent=2)

        if products:
            import pandas as pd
            df = pd.DataFrame(products)
            df.to_csv('data/tienda_inglesa_almacen_products.csv', index=False, encoding='utf-8')

        print(f"💾 Saved to:")
        print(f"   • data/tienda_inglesa_almacen_products.json")
        print(f"   • data/tienda_inglesa_almacen_products.csv")

        return products

    except Exception as e:
        print(f"❌ Error: {e}")
        return []

    finally:
        if driver:
            driver.quit()


def main():
    print("📈 EXPANDING PRODUCT EXTRACTION STRATEGY")
    print("=" * 60)

    # Step 1: Analyze available categories
    category_results = analyze_tienda_inglesa_categories()

    # Step 2: Extract products from promising category
    products = test_broad_product_extraction()

    print(f"\n🎯 EXPANSION RESULTS:")
    print(f"   Categories analyzed: {len(category_results)}")
    print(f"   Products extracted: {len(products)}")

    if len(products) > 10:
        print(f"   🎉 SUCCESS! Significantly more products than lacteos-only approach")

    return products


if __name__ == "__main__":
    products = main()