"""
FINAL PRODUCTION SCRAPER - Tienda Inglesa
Using proven URL patterns and pagination
Target: 200+ products with barcodes
"""
import time
import random
import json
import re
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd


class FinalTiendaInglesaScraper:
    """Production scraper using correct URL patterns"""
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.driver = None
        self.products = []
        self.seen_urls = set()
    
    def create_browser(self):
        """Create stealth browser"""
        options = Options()
        if self.headless:
            options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.binary_location = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver
    
    def human_delay(self, min_sec: float = 2, max_sec: float = 4):
        """Random human-like delay"""
        time.sleep(random.uniform(min_sec, max_sec))
    
    def scrape_category_page(self, category: str, category_id: int, page_num: int = 0) -> List[Dict]:
        """Scrape a category page using correct URL pattern"""
        url = f"https://www.tiendainglesa.com.uy/supermercado/categoria/{category}/busqueda?0,0,*%3A*,{category_id},0,0,rel,,false,,,,{page_num}"
        
        print(f"\n  📄 Page {page_num + 1}: Scraping...")
        
        self.driver.get(url)
        self.human_delay(3, 5)
        
        # Scroll to load all products
        for _ in range(3):
            self.driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(0.5)
        
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        
        # Find all product containers
        containers = soup.select('.card-product-container')
        print(f"     Found {len(containers)} product containers")
        
        page_products = []
        
        for container in containers:
            product = self.extract_product_from_container(container)
            if product and product['url'] not in self.seen_urls:
                page_products.append(product)
                self.seen_urls.add(product['url'])
        
        print(f"     ✅ Extracted {len(page_products)} new products")
        
        return page_products
    
    def extract_product_from_container(self, container) -> Optional[Dict]:
        """Extract product info from container"""
        try:
            # Name
            name_elem = container.select_one('.card-product-name, .card-product-name-and-price')
            if not name_elem:
                return None
            
            name_text = name_elem.get_text().strip()
            # Remove price if present
            if '$' in name_text:
                name_text = name_text.split('$')[0].strip()
            
            # Price
            price = None
            price_elem = container.select_one('.ProductPrice')
            if price_elem:
                price_text = price_elem.get_text().strip()
                price_match = re.search(r'[\d.,]+', price_text.replace('$', '').strip())
                if price_match:
                    try:
                        price = float(price_match.group().replace(',', '.'))
                    except:
                        pass
            
            # Image
            image_url = None
            img_elem = container.select_one('.card-product-img')
            if img_elem:
                src = img_elem.get('src') or img_elem.get('data-src')
                if src and 'http' in src:
                    image_url = src
            
            # URL
            product_url = None
            link_elem = container.select_one('a[href*="producto"]')
            if link_elem:
                href = link_elem.get('href')
                if href:
                    product_url = href if href.startswith('http') else f"https://www.tiendainglesa.com.uy{href}"
            
            if not product_url:
                return None
            
            return {
                'supermarket': 'Tienda Inglesa',
                'name': name_text,
                'price': price,
                'image_url': image_url,
                'url': product_url,
                'barcode': None
            }
            
        except Exception as e:
            return None
    
    def extract_barcode(self, product_url: str) -> Optional[str]:
        """Extract barcode from product page JSON-LD"""
        try:
            self.driver.get(product_url)
            self.human_delay(1, 2)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Look for JSON-LD
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    barcode = data.get('gtin13') or data.get('gtin') or data.get('ean') or data.get('sku')
                    if barcode and str(barcode).isdigit():
                        return str(barcode)
                except:
                    pass
            
            return None
        except Exception as e:
            return None
    
    def scrape_with_pagination(self, category: str = 'almacen', category_id: int = 78, 
                               max_pages: int = 4, extract_barcodes: bool = True):
        """Scrape multiple pages with pagination"""
        print("\n" + "🛒"*40)
        print("TIENDA INGLESA PRODUCTION SCRAPER")
        print("🛒"*40)
        print(f"\nCategory: {category} (ID: {category_id})")
        print(f"Pages to scrape: {max_pages}")
        print(f"Extract barcodes: {extract_barcodes}")
        print(f"Expected products: ~{max_pages * 60}")
        
        # Start browser
        print("\n🌐 Starting browser...")
        self.driver = self.create_browser()
        print("   ✅ Browser ready")
        
        try:
            # Scrape pages
            print(f"\n📦 SCRAPING {max_pages} PAGES:")
            print("="*80)
            
            for page_num in range(max_pages):
                page_products = self.scrape_category_page(category, category_id, page_num)
                self.products.extend(page_products)
                
                print(f"     Total products so far: {len(self.products)}")
                
                # Human delay between pages
                if page_num < max_pages - 1:
                    self.human_delay(2, 4)
            
            print(f"\n✅ Scraping complete: {len(self.products)} products collected")
            
            # Extract barcodes
            if extract_barcodes and self.products:
                print(f"\n🏷️  EXTRACTING BARCODES:")
                print("="*80)
                print(f"This will take ~{len(self.products) * 2 / 60:.0f} minutes...")
                
                barcodes_found = 0
                for i, product in enumerate(self.products, 1):
                    if i % 20 == 0:
                        print(f"   Progress: {i}/{len(self.products)} ({i*100//len(self.products)}%)")
                    
                    barcode = self.extract_barcode(product['url'])
                    if barcode:
                        product['barcode'] = barcode
                        barcodes_found += 1
                    
                    # Small delay
                    time.sleep(0.5)
                
                print(f"\n✅ Barcodes extracted: {barcodes_found}/{len(self.products)} ({barcodes_found*100//len(self.products)}%)")
            
            # Save results
            self.save_results()
            
            return self.products
            
        finally:
            if self.driver:
                self.driver.quit()
    
    def save_results(self):
        """Save scraped products"""
        if not self.products:
            print("\n⚠️  No products to save")
            return
        
        # JSON
        with open('data/tienda_final_products.json', 'w', encoding='utf-8') as f:
            json.dump(self.products, f, ensure_ascii=False, indent=2)
        
        # CSV
        df = pd.DataFrame(self.products)
        df.to_csv('data/tienda_final_products.csv', index=False, encoding='utf-8')
        
        print(f"\n💾 Results saved:")
        print(f"   • data/tienda_final_products.json")
        print(f"   • data/tienda_final_products.csv")
        
        # Stats
        print(f"\n📊 STATISTICS:")
        print(f"   Total products: {len(self.products)}")
        print(f"   With prices: {sum(1 for p in self.products if p.get('price'))}")
        print(f"   With barcodes: {sum(1 for p in self.products if p.get('barcode'))}")
        print(f"   With images: {sum(1 for p in self.products if p.get('image_url'))}")
        
        # Sample
        print(f"\n🥫 SAMPLE PRODUCTS (First 5):")
        print("-" * 80)
        for i, p in enumerate(self.products[:5], 1):
            print(f"\n{i}. {p['name'][:60]}")
            print(f"   💰 ${p.get('price', 'N/A')}")
            print(f"   🏷️  Barcode: {p.get('barcode', 'Not extracted')}")


def main():
    """Run the scraper"""
    print("\n" + "="*80)
    print("TIENDA INGLESA - FINAL PRODUCTION RUN")
    print("="*80)
    print("\nConfiguration:")
    print("  • Category: almacen (ID: 78)")
    print("  • Pages: 4 (60 products each)")
    print("  • Target: 240 products")
    print("  • Extract barcodes: Yes")
    print("\nEstimated time: 10-15 minutes")
    print("\nPress Ctrl+C to cancel or wait 3 seconds...")
    
    time.sleep(3)
    
    scraper = FinalTiendaInglesaScraper(headless=False)
    products = scraper.scrape_with_pagination(
        category='almacen',
        category_id=78,
        max_pages=4,
        extract_barcodes=True
    )
    
    print("\n" + "🎉"*40)
    print("SCRAPING COMPLETE!")
    print("🎉"*40)
    print(f"\n✅ Total products: {len(products)}")
    print(f"📂 Check: data/tienda_final_products.json")
    
    return products


if __name__ == "__main__":
    products = main()
