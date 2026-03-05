"""
Production-ready Tienda Inglesa scraper with multiple strategies
Combines category-based scraping with search fallback for maximum reliability
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


class TiendaInglesaScraper:
    """Production scraper for Tienda Inglesa with anti-bot protection"""
    
    DAIRY_CATEGORIES = [
        'https://www.tiendainglesa.com.uy/supermercado/categoria/1/lacteos-huevos-y-refrigerados',
        'https://www.tiendainglesa.com.uy/supermercado/categoria/2/leches-y-leches-modificadas',
        'https://www.tiendainglesa.com.uy/supermercado/categoria/3/yogures-y-postres',
        'https://www.tiendainglesa.com.uy/supermercado/categoria/4/quesos',
        'https://www.tiendainglesa.com.uy/supermercado/categoria/5/mantecas-margarinas-y-cremas',
        'https://www.tiendainglesa.com.uy/supermercado/categoria/6/dulce-de-leche'
    ]
    
    SEARCH_TERMS = [
        'leche', 'yogur', 'queso', 'manteca', 'crema',
        'dulce de leche', 'conaprole', 'parmalat', 'calcar'
    ]
    
    DAIRY_BRANDS = {
        'conaprole': 'Conaprole',
        'parmalat': 'Parmalat',
        'calcar': 'Calcar',
        'sancor': 'Sancor',
        'talar': 'Talar',
        'serenisima': 'La Serenísima',
        'la serenísima': 'La Serenísima',
        'claldy': 'Claldy',
        'milky': 'Milky',
        'colonial': 'Colonial',
        'colonia': 'Colonia'
    }
    
    def __init__(self, headless: bool = False, max_products: int = 100):
        self.headless = headless
        self.max_products = max_products
        self.driver = None
        self.products = []
        self.seen_products = set()
    
    def create_stealth_browser(self):
        """Create a stealth browser instance"""
        options = Options()
        
        # Stealth options
        if self.headless:
            options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-automation')
        options.add_argument('--disable-plugins')
        
        # Realistic browser profile
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--lang=es-UY,es;q=0.9')
        options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Additional stealth
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--disable-web-security')
        options.add_argument('--allow-running-insecure-content')
        
        # Chrome binary
        options.binary_location = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # Anti-detection scripts
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    def human_like_delay(self, min_seconds: float = 2, max_seconds: float = 5):
        """Add random human-like delays"""
        time.sleep(random.uniform(min_seconds, max_seconds))
    
    def scroll_page(self, times: int = 3):
        """Scroll page gradually like a human"""
        for i in range(times):
            scroll_height = random.randint(300, 700)
            self.driver.execute_script(f"window.scrollBy(0, {scroll_height});")
            time.sleep(random.uniform(0.5, 1.5))
    
    def extract_product_from_element(self, element) -> Optional[Dict]:
        """Extract product data from HTML element"""
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
                'description': None,
                'category': None
            }
            
            # Extract name
            name_elem = element.select_one('.card-product-name, .product-name, .title')
            if name_elem:
                product['name'] = name_elem.get_text().strip()
            
            # Extract price
            price_elem = element.select_one('.ProductPrice, .price, .precio')
            if price_elem:
                price_text = price_elem.get_text().strip()
                product['original_price'] = price_text
                
                # Parse numeric price
                price_match = re.search(r'[\d.,]+', price_text.replace('$', '').strip())
                if price_match:
                    try:
                        product['price'] = float(price_match.group().replace(',', '.'))
                    except:
                        pass
            
            # Extract image
            img_elem = element.select_one('img.card-product-img, img.product-img, img')
            if img_elem:
                src = img_elem.get('src') or img_elem.get('data-src') or img_elem.get('data-lazy')
                if src and 'http' in src:
                    product['image_url'] = src
            
            # Extract URL
            link_elem = element.select_one('a[href*="producto"], a')
            if link_elem:
                href = link_elem.get('href')
                if href:
                    product['url'] = href if href.startswith('http') else f"https://www.tiendainglesa.com.uy{href}"
            
            # Extract brand from name
            if product['name']:
                name_lower = product['name'].lower()
                for brand_key, brand_name in self.DAIRY_BRANDS.items():
                    if brand_key in name_lower:
                        product['brand'] = brand_name
                        break
                
                # Fallback: use first capitalized word
                if not product['brand']:
                    words = product['name'].split()
                    if words and len(words[0]) > 2 and words[0][0].isupper():
                        product['brand'] = words[0]
            
            # Generate unique key for deduplication
            if product['name']:
                product_key = re.sub(r'[^\w\s]', '', product['name'].lower())
                product_key = re.sub(r'\s+', '', product_key)
                return product, product_key
            
            return None, None
            
        except Exception as e:
            print(f"      Error extracting product: {e}")
            return None, None
    
    def is_dairy_product(self, name: str) -> bool:
        """Check if product is dairy"""
        if not name:
            return False
        
        name_lower = name.lower()
        
        # Dairy keywords
        dairy_keywords = [
            'leche', 'milk', 'yogur', 'yogurt', 'queso', 'cheese',
            'manteca', 'butter', 'crema', 'cream', 'ricotta',
            'mozzarella', 'cheddar', 'parmesano', 'dulce de leche',
            'natilla', 'flan', 'casancrem', 'postres'
        ]
        
        # Exclusions
        exclusions = [
            'chocolate', 'helado', 'alfajor', 'torta', 'cookie',
            'galleta', 'aceite', 'vinagre', 'pasta', 'empanada'
        ]
        
        has_dairy = any(keyword in name_lower for keyword in dairy_keywords)
        has_dairy_brand = any(brand in name_lower for brand in self.DAIRY_BRANDS.keys())
        has_exclusion = any(exclusion in name_lower for exclusion in exclusions)
        
        return (has_dairy or has_dairy_brand) and not has_exclusion
    
    def scrape_category_page(self, url: str, category_name: str = None) -> int:
        """Scrape products from a category page"""
        products_found = 0
        
        try:
            print(f"\n  📂 Category: {category_name or url}")
            self.driver.get(url)
            self.human_like_delay(3, 5)
            
            # Scroll to load lazy content
            self.scroll_page(3)
            
            # Parse page
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Find product containers
            containers = soup.select('.card-product-container, .product-card, .product-item, [class*="product"]')
            print(f"    Found {len(containers)} product containers")
            
            for container in containers:
                if len(self.products) >= self.max_products:
                    break
                
                product, product_key = self.extract_product_from_element(container)
                
                if product and product_key and product_key not in self.seen_products:
                    if self.is_dairy_product(product['name']):
                        product['category'] = category_name
                        self.products.append(product)
                        self.seen_products.add(product_key)
                        products_found += 1
                        print(f"      ✓ {product['name'][:60]}... ${product.get('price', 'N/A')}")
            
            print(f"    ✅ Found {products_found} dairy products")
            return products_found
            
        except Exception as e:
            print(f"    ❌ Error scraping category: {e}")
            return 0
    
    def scrape_search_term(self, term: str) -> int:
        """Scrape products from search results"""
        products_found = 0
        
        try:
            print(f"\n  🔍 Searching: '{term}'")
            search_url = f"https://www.tiendainglesa.com.uy/supermercado/buscar?texto={term}"
            self.driver.get(search_url)
            self.human_like_delay(3, 5)
            
            # Scroll to load more
            self.scroll_page(2)
            
            # Parse page
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            containers = soup.select('.card-product-container, .product-card, [class*="product"]')
            
            for container in containers[:15]:  # Limit per search
                if len(self.products) >= self.max_products:
                    break
                
                product, product_key = self.extract_product_from_element(container)
                
                if product and product_key and product_key not in self.seen_products:
                    if self.is_dairy_product(product['name']):
                        product['category'] = f"Search: {term}"
                        self.products.append(product)
                        self.seen_products.add(product_key)
                        products_found += 1
                        print(f"      ✓ {product['name'][:60]}...")
            
            print(f"    ✅ Found {products_found} products for '{term}'")
            return products_found
            
        except Exception as e:
            print(f"    ❌ Error searching '{term}': {e}")
            return 0
    
    def scrape_with_strategy(self, strategy: str = 'hybrid') -> List[Dict]:
        """
        Main scraping method with different strategies
        
        Strategies:
        - 'category': Try known category URLs
        - 'search': Use search functionality
        - 'hybrid': Try categories first, then search for more
        """
        print("🥛 TIENDA INGLESA PRODUCTION SCRAPER")
        print("=" * 70)
        
        try:
            # Initialize browser
            print("\n🌐 Starting stealth browser...")
            self.driver = self.create_stealth_browser()
            
            # Warm up - visit home page first
            print("   Warming up browser...")
            self.driver.get('https://www.google.com')
            self.human_like_delay(1, 2)
            self.driver.get('https://www.tiendainglesa.com.uy')
            self.human_like_delay(3, 5)
            print("   ✓ Browser ready")
            
            # Strategy execution
            if strategy in ['category', 'hybrid']:
                print(f"\n📂 STRATEGY 1: Category-based scraping")
                for i, url in enumerate(self.DAIRY_CATEGORIES, 1):
                    if len(self.products) >= self.max_products:
                        break
                    
                    category_name = f"Category {i}"
                    self.scrape_category_page(url, category_name)
                    self.human_like_delay(2, 4)
            
            if strategy in ['search', 'hybrid']:
                if len(self.products) < self.max_products:
                    print(f"\n🔍 STRATEGY 2: Search-based scraping")
                    for term in self.SEARCH_TERMS:
                        if len(self.products) >= self.max_products:
                            break
                        
                        self.scrape_search_term(term)
                        self.human_like_delay(2, 4)
            
            # Results summary
            print(f"\n{'='*70}")
            print(f"📊 SCRAPING COMPLETE")
            print(f"{'='*70}")
            print(f"Total unique dairy products found: {len(self.products)}")
            print(f"Products with prices: {sum(1 for p in self.products if p.get('price'))}")
            print(f"Products with images: {sum(1 for p in self.products if p.get('image_url'))}")
            print(f"Products with URLs: {sum(1 for p in self.products if p.get('url'))}")
            
            return self.products
            
        except Exception as e:
            print(f"\n❌ Fatal error: {e}")
            import traceback
            traceback.print_exc()
            return self.products
        
        finally:
            if self.driver:
                self.driver.quit()
    
    def save_results(self, filename_prefix: str = 'tienda_inglesa_products'):
        """Save scraped products to JSON and CSV"""
        if not self.products:
            print("\n⚠️  No products to save")
            return
        
        # Save JSON
        json_file = f"data/{filename_prefix}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.products, f, ensure_ascii=False, indent=2)
        
        # Save CSV
        csv_file = f"data/{filename_prefix}.csv"
        df = pd.DataFrame(self.products)
        df.to_csv(csv_file, index=False, encoding='utf-8')
        
        print(f"\n💾 Results saved:")
        print(f"   • {json_file}")
        print(f"   • {csv_file}")
        
        # Display sample
        if self.products:
            print(f"\n🥛 SAMPLE PRODUCTS:")
            print("-" * 70)
            for i, product in enumerate(self.products[:10], 1):
                print(f"{i:2d}. {product['name']}")
                print(f"     💰 ${product.get('price', 'N/A')} | 🏷️ {product.get('brand', 'N/A')}")
                if product.get('category'):
                    print(f"     📂 {product['category']}")


def main():
    """Run the scraper"""
    scraper = TiendaInglesaScraper(
        headless=False,  # Set to True for production
        max_products=100
    )
    
    # Use hybrid strategy (best results)
    products = scraper.scrape_with_strategy(strategy='hybrid')
    
    # Save results
    scraper.save_results('tienda_inglesa_production')
    
    return products


if __name__ == "__main__":
    products = main()
    print(f"\n🎉 Done! Scraped {len(products)} dairy products from Tienda Inglesa")
