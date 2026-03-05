"""
Category-Focused Scraper: ARROZ (Rice)
Scrape rice products from all 3 supermarkets for better matching
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
from difflib import SequenceMatcher


class RiceCategoryScraper:
    """Scrape rice products from all supermarkets"""
    
    def __init__(self):
        self.driver = None
        self.tienda_products = []
        self.disco_products = []
        self.devoto_products = []
    
    def create_browser(self):
        """Create stealth browser"""
        options = Options()
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
    
    def human_delay(self, min_sec: float = 1, max_sec: float = 3):
        """Random human-like delay"""
        time.sleep(random.uniform(min_sec, max_sec))
    
    def scrape_tienda_rice(self, max_pages: int = 3):
        """Scrape Tienda Inglesa rice category"""
        print(f"\n🛒 SCRAPING TIENDA INGLESA - ARROZ Y LEGUMBRES")
        print("="*80)
        
        # Category: almacen/arroz-legumbres (78/84)
        base_url = "https://www.tiendainglesa.com.uy/supermercado/categoria/almacen/arroz-legumbres/busqueda?0,0,*%3A*,78,84,0,,,false,,,,"
        
        for page in range(max_pages):
            url = f"{base_url}{page}"
            print(f"\n  📄 Page {page + 1}: {url}")
            
            self.driver.get(url)
            self.human_delay(3, 5)
            
            # Scroll
            for _ in range(3):
                self.driver.execute_script("window.scrollBy(0, 500);")
                time.sleep(0.5)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            containers = soup.select('.card-product-container')
            
            print(f"     Found {len(containers)} products")
            
            for container in containers:
                product = self.extract_tienda_product(container)
                if product:
                    self.tienda_products.append(product)
            
            self.human_delay(2, 4)
        
        print(f"\n✅ Tienda Inglesa total: {len(self.tienda_products)} products")
    
    def extract_tienda_product(self, container) -> Optional[Dict]:
        """Extract Tienda product"""
        try:
            # Name
            name_elem = container.select_one('.card-product-name, .card-product-name-and-price')
            if not name_elem:
                return None
            
            name = name_elem.get_text().strip()
            if '$' in name:
                name = name.split('$')[0].strip()
            
            # Price
            price = None
            price_elem = container.select_one('.ProductPrice')
            if price_elem:
                price_text = price_elem.get_text().strip()
                match = re.search(r'[\d.,]+', price_text.replace('$', ''))
                if match:
                    try:
                        price = float(match.group().replace(',', '.'))
                    except:
                        pass
            
            # URL
            url = None
            link = container.select_one('a[href*="producto"]')
            if link:
                href = link.get('href')
                if href:
                    url = href if href.startswith('http') else f"https://www.tiendainglesa.com.uy{href}"
            
            # Image
            image_url = None
            img = container.select_one('.card-product-img')
            if img:
                image_url = img.get('src') or img.get('data-src')
            
            if not url:
                return None
            
            return {
                'supermarket': 'Tienda Inglesa',
                'name': name,
                'price': price,
                'url': url,
                'image_url': image_url,
                'barcode': None
            }
        except:
            return None
    
    def scrape_disco_rice(self, max_pages: int = 3):
        """Scrape Disco rice category"""
        print(f"\n🛒 SCRAPING DISCO - ARROZ")
        print("="*80)
        
        base_url = "https://www.disco.com.uy/products/category/arroz/101013"
        
        for page in range(max_pages):
            url = f"{base_url}?page={page}" if page > 0 else base_url
            print(f"\n  📄 Page {page + 1}: {url}")
            
            self.driver.get(url)
            self.human_delay(3, 5)
            
            # Scroll
            for _ in range(3):
                self.driver.execute_script("window.scrollBy(0, 800);")
                time.sleep(0.5)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            products = self.extract_disco_devoto_products(soup, 'Disco')
            
            print(f"     Found {len(products)} products")
            self.disco_products.extend(products)
            
            self.human_delay(2, 4)
        
        print(f"\n✅ Disco total: {len(self.disco_products)} products")
    
    def scrape_devoto_rice(self, max_pages: int = 3):
        """Scrape Devoto rice category"""
        print(f"\n🛒 SCRAPING DEVOTO - ARROZ")
        print("="*80)
        
        base_url = "https://www.devoto.com.uy/products/category/arroz/101013"
        
        for page in range(max_pages):
            url = f"{base_url}?page={page}" if page > 0 else base_url
            print(f"\n  📄 Page {page + 1}: {url}")
            
            self.driver.get(url)
            self.human_delay(3, 5)
            
            # Scroll
            for _ in range(3):
                self.driver.execute_script("window.scrollBy(0, 800);")
                time.sleep(0.5)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            products = self.extract_disco_devoto_products(soup, 'Devoto')
            
            print(f"     Found {len(products)} products")
            self.devoto_products.extend(products)
            
            self.human_delay(2, 4)
        
        print(f"\n✅ Devoto total: {len(self.devoto_products)} products")
    
    def extract_disco_devoto_products(self, soup, supermarket: str) -> List[Dict]:
        """Extract products from Disco/Devoto"""
        products = []
        
        selectors = [
            'article.product',
            '.product-card',
            '[data-product]',
            '.shelf-item',
            'div[class*="product"]'
        ]
        
        containers = []
        for selector in selectors:
            containers = soup.select(selector)
            if containers:
                break
        
        for container in containers:
            try:
                # Name
                name = None
                name_selectors = ['.product-name', '.product-title', 'h2', 'h3', '[class*="name"]']
                for sel in name_selectors:
                    elem = container.select_one(sel)
                    if elem:
                        name = elem.get_text().strip()
                        break
                
                if not name:
                    continue
                
                # Price
                price = None
                price_selectors = ['.price', '[class*="price"]', '[class*="Price"]']
                for sel in price_selectors:
                    elem = container.select_one(sel)
                    if elem:
                        price_text = elem.get_text().strip()
                        match = re.search(r'[\d.,]+', price_text.replace('$', ''))
                        if match:
                            try:
                                price = float(match.group().replace(',', '.'))
                                break
                            except:
                                pass
                
                # URL
                url = None
                link = container.find('a', href=True)
                if link:
                    href = link.get('href')
                    if href:
                        if href.startswith('http'):
                            url = href
                        elif href.startswith('/'):
                            base = f'https://www.{supermarket.lower()}.com.uy'
                            url = base + href
                
                # Image
                image_url = None
                img = container.find('img')
                if img:
                    image_url = img.get('src') or img.get('data-src')
                
                products.append({
                    'supermarket': supermarket,
                    'name': name,
                    'price': price,
                    'url': url,
                    'image_url': image_url,
                    'barcode': None
                })
            except:
                continue
        
        return products
    
    def extract_barcodes(self, products: List[Dict], store_name: str):
        """Extract barcodes from product pages"""
        print(f"\n🏷️  EXTRACTING BARCODES: {store_name}")
        print("="*80)
        
        found = 0
        total = len(products)
        
        for i, product in enumerate(products, 1):
            if i % 10 == 0:
                print(f"   Progress: {i}/{total} ({i*100//total}%) - Found: {found}")
            
            url = product.get('url')
            if not url:
                continue
            
            try:
                self.driver.get(url)
                self.human_delay(1, 2)
                
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                
                # Look for JSON-LD
                scripts = soup.find_all('script', type='application/ld+json')
                for script in scripts:
                    try:
                        data = json.loads(script.string)
                        barcode = data.get('gtin13') or data.get('gtin') or data.get('ean')
                        if barcode and str(barcode).isdigit():
                            product['barcode'] = str(barcode)
                            found += 1
                            break
                    except:
                        pass
                
                time.sleep(0.5)
            except:
                continue
        
        print(f"\n✅ {store_name}: {found}/{total} barcodes extracted")
        return found
    
    def match_products(self, threshold: float = 0.65):
        """Match products across stores"""
        print("\n🔗 MATCHING PRODUCTS...")
        print("="*80)
        
        matches = []
        all_other = self.disco_products + self.devoto_products
        
        for tienda_prod in self.tienda_products:
            tienda_name = tienda_prod['name'].lower()
            tienda_barcode = tienda_prod.get('barcode')
            
            matched_products = []
            
            for other_prod in all_other:
                # Match by barcode first (if available)
                if tienda_barcode and other_prod.get('barcode'):
                    if tienda_barcode == other_prod['barcode']:
                        matched_products.append({
                            'product': other_prod,
                            'score': 1.0,
                            'match_type': 'barcode'
                        })
                        continue
                
                # Match by name similarity
                other_name = other_prod['name'].lower()
                similarity = SequenceMatcher(None, tienda_name, other_name).ratio()
                
                if similarity >= threshold:
                    matched_products.append({
                        'product': other_prod,
                        'score': similarity,
                        'match_type': 'name'
                    })
            
            if matched_products:
                matched_products.sort(key=lambda x: x['score'], reverse=True)
                
                matches.append({
                    'tienda_product': tienda_prod,
                    'matched_products': [m['product'] for m in matched_products],
                    'scores': [m['score'] for m in matched_products],
                    'match_types': [m['match_type'] for m in matched_products]
                })
        
        print(f"\n✅ Found {len(matches)} matches!")
        return matches
    
    def create_comparison_report(self, matches: List[Dict]):
        """Create price comparison report"""
        print("\n📊 CREATING COMPARISON REPORT...")
        print("="*80)
        
        comparison_data = []
        
        for match in matches:
            tienda = match['tienda_product']
            
            for i, other in enumerate(match['matched_products']):
                t_price = tienda.get('price')
                o_price = other.get('price')
                
                if t_price and o_price:
                    diff = o_price - t_price
                    pct = (abs(diff) / t_price) * 100
                    cheaper = 'Tienda Inglesa' if t_price < o_price else other['supermarket']
                    
                    comparison_data.append({
                        'Product_Tienda': tienda['name'][:60],
                        'Product_Other': other['name'][:60],
                        'Store': other['supermarket'],
                        'Price_Tienda': f"${t_price:.0f}",
                        'Price_Other': f"${o_price:.0f}",
                        'Difference': f"${abs(diff):.0f}",
                        'Percentage': f"{pct:.1f}%",
                        'Cheaper_At': cheaper,
                        'Match_Score': f"{match['scores'][i]:.2f}",
                        'Match_Type': match['match_types'][i],
                        'Savings': abs(diff) if t_price < o_price else -abs(diff)
                    })
        
        if comparison_data:
            df = pd.DataFrame(comparison_data)
            df.to_csv('results/rice_comparison.csv', index=False, encoding='utf-8')
            
            print(f"   ✅ Saved: results/rice_comparison.csv")
            print(f"\n📊 STATISTICS:")
            print(f"   • Total matches: {len(matches)}")
            print(f"   • Price comparisons: {len(comparison_data)}")
            
            tienda_cheaper = sum(1 for row in comparison_data if row['Cheaper_At'] == 'Tienda Inglesa')
            others_cheaper = len(comparison_data) - tienda_cheaper
            
            print(f"   • Tienda Inglesa cheaper: {tienda_cheaper} ({tienda_cheaper*100//len(comparison_data) if comparison_data else 0}%)")
            print(f"   • Others cheaper: {others_cheaper} ({others_cheaper*100//len(comparison_data) if comparison_data else 0}%)")
            
            # Top savings
            df_sorted = df.sort_values('Savings', ascending=False)
            print(f"\n💰 TOP 10 BEST DEALS:")
            print("-"*80)
            for idx, row in df_sorted.head(10).iterrows():
                print(f"\n{list(df_sorted.head(10).index).index(idx)+1}. {row['Product_Tienda']}")
                print(f"   Tienda: {row['Price_Tienda']} vs {row['Store']}: {row['Price_Other']}")
                print(f"   💰 {row['Cheaper_At']} - Save: {row['Difference']} ({row['Percentage']})")
        else:
            print("   ⚠️  No comparisons available")
    
    def run(self):
        """Run the rice category scraper"""
        print("\n" + "🍚"*40)
        print("RICE CATEGORY SCRAPER")
        print("🍚"*40)
        print("\nScraping rice products from all 3 supermarkets")
        print("Expected: High match rate due to same category!")
        print("\nStarting in 3 seconds...")
        time.sleep(3)
        
        # Start browser
        print("\n🌐 Starting browser...")
        self.driver = self.create_browser()
        print("   ✅ Browser ready")
        
        try:
            # Scrape all stores
            self.scrape_tienda_rice(max_pages=3)
            self.scrape_disco_rice(max_pages=3)
            self.scrape_devoto_rice(max_pages=3)
            
            print("\n" + "="*80)
            print("PHASE 1 COMPLETE - PRODUCTS SCRAPED")
            print("="*80)
            print(f"   • Tienda Inglesa: {len(self.tienda_products)}")
            print(f"   • Disco: {len(self.disco_products)}")
            print(f"   • Devoto: {len(self.devoto_products)}")
            print(f"   • Total: {len(self.tienda_products) + len(self.disco_products) + len(self.devoto_products)}")
            
            # Extract barcodes for Tienda
            print("\n" + "="*80)
            print("PHASE 2 - EXTRACTING BARCODES")
            print("="*80)
            self.extract_barcodes(self.tienda_products, 'Tienda Inglesa')
            
            # Match products
            print("\n" + "="*80)
            print("PHASE 3 - MATCHING")
            print("="*80)
            matches = self.match_products(threshold=0.65)
            
            # Save all data
            all_products = self.tienda_products + self.disco_products + self.devoto_products
            with open('data/rice_products.json', 'w', encoding='utf-8') as f:
                json.dump(all_products, f, ensure_ascii=False, indent=2)
            
            with open('results/rice_matches.json', 'w', encoding='utf-8') as f:
                json.dump(matches, f, ensure_ascii=False, indent=2)
            
            # Create report
            self.create_comparison_report(matches)
            
            print("\n" + "🎉"*40)
            print("RICE CATEGORY SCRAPING COMPLETE!")
            print("🎉"*40)
            
            return matches
            
        finally:
            if self.driver:
                self.driver.quit()


def main():
    scraper = RiceCategoryScraper()
    matches = scraper.run()
    
    print(f"\n✅ Success! Found {len(matches)} matched products")
    print(f"📂 Check results/rice_comparison.csv")


if __name__ == "__main__":
    main()
