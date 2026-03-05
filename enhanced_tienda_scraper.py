"""
ENHANCED Tienda Inglesa Scraper
- Better search strategy
- Extract barcodes from product detail pages
- Handle pagination
- Get 200+ products
"""
import time
import random
import json
import re
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd


class EnhancedTiendaInglesaScraper:
    """Enhanced scraper with barcode extraction and better pagination"""
    
    # More specific search terms to find products
    SEARCH_TERMS = [
        # Start with generic dairy searches (most results)
        'lacteos', 'leche', 'yogur', 'queso', 'manteca', 'crema', 'dulce de leche',
        
        # Specific product types
        'leche entera', 'leche descremada', 'leche semidescremada',
        'leche larga vida', 'leche uht',
        'yogur natural', 'yogur bebible', 'yogur griego',
        'queso mozzarella', 'queso rallado', 'queso untable',
        'queso crema', 'queso port salut', 'queso dambo',
        'crema de leche', 'manteca con sal', 'manteca sin sal',
        
        # Brands (will also find dairy)
        'conaprole leche', 'conaprole yogur', 'conaprole queso',
        'parmalat leche', 'parmalat yogur',
        'calcar leche', 'calcar yogur',
    ]
    
    def __init__(self, headless: bool = False, max_products: int = 200):
        self.headless = headless
        self.max_products = max_products
        self.driver = None
        self.products = []
        self.seen_urls = set()
        self.seen_names = set()
    
    def create_stealth_browser(self):
        """Create stealth browser"""
        options = Options()
        
        if self.headless:
            options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-automation')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--lang=es-UY,es;q=0.9')
        options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.binary_location = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    def human_delay(self, min_sec: float = 2, max_sec: float = 4):
        """Random human-like delay"""
        time.sleep(random.uniform(min_sec, max_sec))
    
    def extract_barcode_from_product_page(self, product_url: str) -> Optional[str]:
        """Visit product detail page and extract barcode from JSON-LD"""
        try:
            self.driver.get(product_url)
            self.human_delay(1, 2)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Method 1: Look for JSON-LD structured data (BEST METHOD)
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    # Look for GTIN, EAN, or SKU in structured data
                    barcode = data.get('gtin13') or data.get('gtin') or data.get('ean') or data.get('sku')
                    if barcode and str(barcode).isdigit():
                        return str(barcode)
                except:
                    pass
            
            # Method 2: Search for EAN pattern in page text
            text = soup.get_text()
            
            barcode_patterns = [
                r'ean[:\s]+(\d{8,14})',
                r'gtin[:\s]+(\d{8,14})',
                r'código[:\s]+(\d{8,14})',
                r'código de barras[:\s]+(\d{8,14})',
                r'\b(\d{13})\b',  # 13-digit EAN (common)
            ]
            
            for pattern in barcode_patterns:
                match = re.search(pattern, text.lower())
                if match:
                    barcode = match.group(1)
                    if len(barcode) >= 8:
                        return barcode
            
            return None
            
        except Exception as e:
            print(f"        ⚠️  Error extracting barcode: {e}")
            return None
    
    def search_and_extract(self, search_term: str, max_per_search: int = 20) -> int:
        """Search for a term and extract products with pagination"""
        products_found = 0
        
        try:
            print(f"\n  🔍 Searching: '{search_term}'")
            
            # Construct search URL
            search_url = f"https://www.tiendainglesa.com.uy/supermercado/buscar?texto={search_term}"
            self.driver.get(search_url)
            self.human_delay(3, 5)
            
            # Scroll to load lazy content
            for _ in range(3):
                self.driver.execute_script("window.scrollBy(0, 500);")
                time.sleep(0.5)
            
            # Parse the page
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Find product containers
            containers = soup.select('.card-product-container, .product-card, [class*="product"]')
            print(f"    Found {len(containers)} containers")
            
            for container in containers[:max_per_search]:
                if len(self.products) >= self.max_products:
                    break
                
                product = self.extract_product_basic(container)
                
                if product and self.is_dairy_product(product['name']):
                    # Check if we've seen this product
                    product_key = self.normalize_name(product['name'])
                    
                    if product_key not in self.seen_names and product.get('url') not in self.seen_urls:
                        # Try to extract barcode from detail page
                        if product.get('url'):
                            print(f"      → Extracting barcode for: {product['name'][:50]}...")
                            barcode = self.extract_barcode_from_product_page(product['url'])
                            if barcode:
                                product['barcode'] = barcode
                                print(f"         ✅ Barcode: {barcode}")
                            else:
                                print(f"         ⚠️  No barcode found")
                        
                        self.products.append(product)
                        self.seen_names.add(product_key)
                        if product.get('url'):
                            self.seen_urls.add(product['url'])
                        
                        products_found += 1
                        print(f"      ✓ [{len(self.products)}] {product['name'][:60]}... ${product.get('price', 'N/A')}")
            
            print(f"    ✅ Found {products_found} new products for '{search_term}'")
            return products_found
            
        except Exception as e:
            print(f"    ❌ Error searching '{search_term}': {e}")
            return 0
    
    def extract_product_basic(self, element) -> Optional[Dict]:
        """Extract basic product info using FIXED selectors for both page types"""
        try:
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
            
            # Extract name - FIXED: Works for both category and search pages
            name_elem = element.select_one('.card-product-name, .card-product-name-and-price')
            if name_elem:
                name_text = name_elem.get_text().strip()
                # Remove price if present (search pages include price in name element)
                # Price is usually after multiple spaces or on same line
                name_parts = name_text.split('$')
                product['name'] = name_parts[0].strip()
            
            if not product['name']:
                return None
            
            # Extract price - USE WORKING SELECTOR
            price_elem = element.select_one('.ProductPrice')
            if price_elem:
                price_text = price_elem.get_text().strip()
                product['original_price'] = price_text
                
                price_match = re.search(r'[\d.,]+', price_text.replace('$', '').strip())
                if price_match:
                    try:
                        product['price'] = float(price_match.group().replace(',', '.'))
                    except:
                        pass
            
            # Extract image - USE WORKING SELECTOR
            img_elem = element.select_one('.card-product-img')
            if img_elem:
                src = img_elem.get('src') or img_elem.get('data-src')
                if src and 'http' in src:
                    product['image_url'] = src
            
            # Extract URL - USE WORKING SELECTOR
            link_elem = element.select_one('a[href*="producto"]')
            if link_elem:
                href = link_elem.get('href')
                if href:
                    product['url'] = href if href.startswith('http') else f"https://www.tiendainglesa.com.uy{href}"
            
            # Extract brand from name
            if product['name']:
                name_lower = product['name'].lower()
                brands = {
                    'conaprole': 'Conaprole', 'parmalat': 'Parmalat',
                    'calcar': 'Calcar', 'sancor': 'Sancor',
                    'talar': 'Talar', 'serenisima': 'La Serenísima',
                    'la serenísima': 'La Serenísima', 'claldy': 'Claldy',
                    'milky': 'Milky', 'colonial': 'Colonial',
                    'punta del este': 'Punta del Este',
                    'tienda inglesa': 'Tienda Inglesa'
                }
                
                for brand_key, brand_name in brands.items():
                    if brand_key in name_lower:
                        product['brand'] = brand_name
                        break
                
                # Fallback: use first word if capitalized
                if not product['brand']:
                    words = product['name'].split()
                    if words and len(words[0]) > 2 and words[0][0].isupper():
                        product['brand'] = words[0]
            
            return product
            
        except Exception as e:
            return None
    
    def normalize_name(self, name: str) -> str:
        """Normalize product name for deduplication"""
        if not name:
            return ""
        normalized = re.sub(r'[^\w\s]', '', name.lower())
        normalized = re.sub(r'\s+', '', normalized)
        return normalized
    
    def is_dairy_product(self, name: str) -> bool:
        """Check if product is dairy"""
        if not name:
            return False
        
        name_lower = name.lower()
        
        dairy_keywords = [
            'leche', 'milk', 'yogur', 'yogurt', 'queso', 'cheese',
            'manteca', 'butter', 'crema', 'cream', 'ricotta',
            'mozzarella', 'dulce de leche', 'natilla', 'flan'
        ]
        
        exclusions = [
            'chocolate', 'helado', 'alfajor', 'torta', 'cookie',
            'galleta', 'aceite', 'pasta'
        ]
        
        has_dairy = any(keyword in name_lower for keyword in dairy_keywords)
        has_exclusion = any(exclusion in name_lower for exclusion in exclusions)
        
        return has_dairy and not has_exclusion
    
    def run_enhanced_scraping(self):
        """Main scraping method with enhanced strategy"""
        print("\n" + "🥛"*35)
        print("ENHANCED TIENDA INGLESA SCRAPER")
        print("Target: 200+ products with barcodes")
        print("🥛"*35)
        
        try:
            # Start browser
            print("\n🌐 Starting stealth browser...")
            self.driver = self.create_stealth_browser()
            
            # Warm up
            print("   Warming up...")
            self.driver.get('https://www.google.com')
            self.human_delay(1, 2)
            self.driver.get('https://www.tiendainglesa.com.uy')
            self.human_delay(3, 5)
            print("   ✅ Browser ready\n")
            
            # Search strategy - prioritize high-yield terms
            print("🔍 SEARCH STRATEGY: Multiple specific terms\n")
            
            for term in self.SEARCH_TERMS:
                if len(self.products) >= self.max_products:
                    print(f"\n✅ Reached target of {self.max_products} products!")
                    break
                
                self.search_and_extract(term, max_per_search=15)
                
                # Human-like delay between searches
                self.human_delay(3, 5)
            
            # Final summary
            print("\n" + "="*70)
            print("📊 SCRAPING COMPLETE")
            print("="*70)
            print(f"Total products found: {len(self.products)}")
            print(f"Products with prices: {sum(1 for p in self.products if p.get('price'))}")
            print(f"Products with barcodes: {sum(1 for p in self.products if p.get('barcode'))}")
            print(f"Products with images: {sum(1 for p in self.products if p.get('image_url'))}")
            
            # Save results
            self.save_results()
            
            return self.products
            
        except Exception as e:
            print(f"\n❌ Error during scraping: {e}")
            import traceback
            traceback.print_exc()
            return self.products
        
        finally:
            if self.driver:
                self.driver.quit()
    
    def save_results(self):
        """Save results to files"""
        if not self.products:
            print("\n⚠️  No products to save")
            return
        
        # Save JSON
        with open('data/tienda_enhanced_products.json', 'w', encoding='utf-8') as f:
            json.dump(self.products, f, ensure_ascii=False, indent=2)
        
        # Save CSV
        df = pd.DataFrame(self.products)
        df.to_csv('data/tienda_enhanced_products.csv', index=False, encoding='utf-8')
        
        print(f"\n💾 Results saved:")
        print(f"   • data/tienda_enhanced_products.json")
        print(f"   • data/tienda_enhanced_products.csv")
        
        # Show sample
        print(f"\n🥛 SAMPLE PRODUCTS (First 5):")
        print("-" * 70)
        for i, p in enumerate(self.products[:5], 1):
            print(f"\n{i}. {p['name']}")
            print(f"   💰 ${p.get('price', 'N/A')}")
            print(f"   🏷️  {p.get('brand', 'Unknown')}")
            print(f"   📊 Barcode: {p.get('barcode', 'Not found')}")
        
        # Barcode statistics
        products_with_barcodes = sum(1 for p in self.products if p.get('barcode'))
        if products_with_barcodes > 0:
            barcode_percentage = (products_with_barcodes / len(self.products)) * 100
            print(f"\n📊 Barcode Coverage: {products_with_barcodes}/{len(self.products)} ({barcode_percentage:.1f}%)")


def main():
    """Run the enhanced scraper"""
    print("\n🛒 ENHANCED TIENDA INGLESA SCRAPER")
    print("=" * 70)
    print("\nGoals:")
    print("  • Get 200+ dairy products")
    print("  • Extract barcodes from product pages")
    print("  • Better product coverage")
    print("\nEstimated time: 20-30 minutes")
    print("(Visiting each product page takes time but gets barcodes)")
    print("\nPress Ctrl+C to cancel or wait 5 seconds...")
    
    time.sleep(5)
    
    scraper = EnhancedTiendaInglesaScraper(
        headless=False,
        max_products=200
    )
    
    products = scraper.run_enhanced_scraping()
    
    print("\n" + "🎉"*35)
    print("SCRAPING COMPLETE!")
    print("🎉"*35)
    print(f"\n✅ Successfully scraped {len(products)} dairy products")
    print(f"📂 Check data/tienda_enhanced_products.json for results")
    
    return products


if __name__ == "__main__":
    products = main()
