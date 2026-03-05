"""
HYBRID MATCHING APPROACH
Phase 1: Scrape categories from Disco & Devoto
Phase 2: Search for unmatched products individually
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


class HybridMatcher:
    """Hybrid approach to match Tienda products with Disco & Devoto"""
    
    def __init__(self):
        self.driver = None
        self.tienda_products = []
        self.disco_products = []
        self.devoto_products = []
        self.matches = []
    
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
    
    def load_tienda_products(self):
        """Load Tienda Inglesa products"""
        print("\n📦 Loading Tienda Inglesa products...")
        with open('data/tienda_final_products.json', 'r', encoding='utf-8') as f:
            self.tienda_products = json.load(f)
        print(f"   ✅ Loaded {len(self.tienda_products)} products")
    
    def scrape_disco_category(self, max_pages: int = 3):
        """Scrape Disco almacen category"""
        print(f"\n🛒 PHASE 1A: Scraping Disco (pages 1-{max_pages})...")
        print("="*80)
        
        base_url = "https://www.disco.com.uy/almacen"
        
        for page in range(max_pages):
            print(f"\n  📄 Page {page + 1}...")
            
            # Disco uses ?page=N for pagination
            url = f"{base_url}?page={page}" if page > 0 else base_url
            
            self.driver.get(url)
            self.human_delay(3, 5)
            
            # Scroll to load products
            for _ in range(3):
                self.driver.execute_script("window.scrollBy(0, 800);")
                time.sleep(0.5)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Find product containers (common selectors for Disco/Devoto)
            products_found = self.extract_products_from_page(soup, 'Disco')
            
            print(f"     ✅ Found {len(products_found)} products")
            self.disco_products.extend(products_found)
            
            self.human_delay(2, 4)
        
        print(f"\n✅ Disco total: {len(self.disco_products)} products")
    
    def scrape_devoto_category(self, max_pages: int = 3):
        """Scrape Devoto almacen category"""
        print(f"\n🛒 PHASE 1B: Scraping Devoto (pages 1-{max_pages})...")
        print("="*80)
        
        base_url = "https://www.devoto.com.uy/almacen"
        
        for page in range(max_pages):
            print(f"\n  📄 Page {page + 1}...")
            
            url = f"{base_url}?page={page}" if page > 0 else base_url
            
            self.driver.get(url)
            self.human_delay(3, 5)
            
            # Scroll to load products
            for _ in range(3):
                self.driver.execute_script("window.scrollBy(0, 800);")
                time.sleep(0.5)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            products_found = self.extract_products_from_page(soup, 'Devoto')
            
            print(f"     ✅ Found {len(products_found)} products")
            self.devoto_products.extend(products_found)
            
            self.human_delay(2, 4)
        
        print(f"\n✅ Devoto total: {len(self.devoto_products)} products")
    
    def extract_products_from_page(self, soup, supermarket: str) -> List[Dict]:
        """Extract products from page HTML"""
        products = []
        
        # Try different selectors
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
            product = self.extract_single_product(container, supermarket)
            if product:
                products.append(product)
        
        return products
    
    def extract_single_product(self, container, supermarket: str) -> Optional[Dict]:
        """Extract single product from container"""
        try:
            # Name
            name = None
            name_selectors = ['.product-name', '.product-title', 'h2', 'h3', '[class*="name"]']
            for selector in name_selectors:
                elem = container.select_one(selector)
                if elem:
                    name = elem.get_text().strip()
                    break
            
            if not name:
                return None
            
            # Price
            price = None
            price_selectors = ['.price', '[class*="price"]', '[class*="Price"]']
            for selector in price_selectors:
                elem = container.select_one(selector)
                if elem:
                    price_text = elem.get_text().strip()
                    match = re.search(r'[\d.,]+', price_text.replace('$', '').strip())
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
                        base = 'https://www.disco.com.uy' if supermarket == 'Disco' else 'https://www.devoto.com.uy'
                        url = base + href
            
            # Image
            image_url = None
            img = container.find('img')
            if img:
                image_url = img.get('src') or img.get('data-src')
            
            return {
                'supermarket': supermarket,
                'name': name,
                'price': price,
                'url': url,
                'image_url': image_url,
                'barcode': None  # Will try to extract later if needed
            }
            
        except Exception as e:
            return None
    
    def match_by_barcode(self):
        """Match products using barcodes (most accurate)"""
        print("\n🔗 MATCHING BY BARCODE...")
        print("="*80)
        
        # Create barcode lookup for other stores
        other_products = self.disco_products + self.devoto_products
        
        barcode_matches = []
        
        for tienda_prod in self.tienda_products:
            barcode = tienda_prod.get('barcode')
            if not barcode:
                continue
            
            # Look for exact barcode match
            matched = [p for p in other_products if p.get('barcode') == barcode]
            
            if matched:
                match_group = {
                    'match_type': 'barcode',
                    'barcode': barcode,
                    'tienda_product': tienda_prod,
                    'other_products': matched
                }
                barcode_matches.append(match_group)
        
        print(f"   ✅ Barcode matches: {len(barcode_matches)}")
        return barcode_matches
    
    def match_by_name_similarity(self, threshold: float = 0.75):
        """Match products using name similarity"""
        print("\n🔗 MATCHING BY NAME SIMILARITY...")
        print("="*80)
        
        other_products = self.disco_products + self.devoto_products
        name_matches = []
        
        # Create a set of already matched barcodes
        matched_barcodes = set()
        for match in self.matches:
            if match.get('barcode'):
                matched_barcodes.add(match['barcode'])
        
        for tienda_prod in self.tienda_products:
            # Skip if already matched by barcode
            if tienda_prod.get('barcode') in matched_barcodes:
                continue
            
            tienda_name = tienda_prod['name'].lower()
            best_matches = []
            
            for other_prod in other_products:
                other_name = other_prod['name'].lower()
                
                # Calculate similarity
                similarity = SequenceMatcher(None, tienda_name, other_name).ratio()
                
                if similarity >= threshold:
                    best_matches.append({
                        'product': other_prod,
                        'similarity': similarity
                    })
            
            if best_matches:
                # Sort by similarity
                best_matches.sort(key=lambda x: x['similarity'], reverse=True)
                
                match_group = {
                    'match_type': 'name_similarity',
                    'tienda_product': tienda_prod,
                    'other_products': [m['product'] for m in best_matches[:3]],  # Top 3
                    'similarity_scores': [m['similarity'] for m in best_matches[:3]]
                }
                name_matches.append(match_group)
        
        print(f"   ✅ Name similarity matches: {len(name_matches)}")
        return name_matches
    
    def create_comparison_report(self):
        """Create final comparison report"""
        print("\n📊 CREATING COMPARISON REPORT...")
        print("="*80)
        
        comparison_data = []
        
        for match in self.matches:
            tienda = match['tienda_product']
            
            for other in match['other_products']:
                t_price = tienda.get('price')
                o_price = other.get('price')
                
                if t_price and o_price:
                    diff = o_price - t_price
                    pct = (abs(diff) / t_price) * 100
                    cheaper = 'Tienda Inglesa' if t_price < o_price else other['supermarket']
                    
                    comparison_data.append({
                        'Product_Tienda': tienda['name'][:50],
                        'Product_Other': other['name'][:50],
                        'Store_Other': other['supermarket'],
                        'Price_Tienda': f"${t_price:.0f}",
                        'Price_Other': f"${o_price:.0f}",
                        'Difference': f"${abs(diff):.0f}",
                        'Percentage': f"{pct:.1f}%",
                        'Cheaper_At': cheaper,
                        'Match_Type': match.get('match_type', 'unknown'),
                        'Barcode': match.get('barcode', 'N/A')
                    })
        
        if comparison_data:
            df = pd.DataFrame(comparison_data)
            df.to_csv('results/hybrid_comparison.csv', index=False, encoding='utf-8')
            
            print(f"   ✅ Saved comparison: results/hybrid_comparison.csv")
            print(f"\n📊 SUMMARY:")
            print(f"   • Total matches: {len(self.matches)}")
            print(f"   • Price comparisons: {len(comparison_data)}")
            
            # Show top 10 differences
            df_sorted = df.sort_values('Difference', key=lambda x: x.str.replace('$', '').astype(float), ascending=False)
            print(f"\n💰 TOP 10 PRICE DIFFERENCES:")
            print("-"*80)
            for idx, row in df_sorted.head(10).iterrows():
                print(f"\n{idx+1}. {row['Product_Tienda']}")
                print(f"   Tienda: {row['Price_Tienda']} | {row['Store_Other']}: {row['Price_Other']}")
                print(f"   Difference: {row['Difference']} ({row['Percentage']})")
                print(f"   Cheaper at: {row['Cheaper_At']}")
        else:
            print("   ⚠️  No price comparisons available")
    
    def save_all_products(self):
        """Save all scraped products"""
        all_products = self.tienda_products + self.disco_products + self.devoto_products
        
        with open('data/all_products_hybrid.json', 'w', encoding='utf-8') as f:
            json.dump(all_products, f, ensure_ascii=False, indent=2)
        
        with open('results/matches_hybrid.json', 'w', encoding='utf-8') as f:
            json.dump(self.matches, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Saved all data:")
        print(f"   • data/all_products_hybrid.json ({len(all_products)} products)")
        print(f"   • results/matches_hybrid.json ({len(self.matches)} matches)")
    
    def run(self):
        """Run the hybrid matching process"""
        print("\n" + "🎯"*40)
        print("HYBRID MATCHING APPROACH")
        print("🎯"*40)
        print("\nPhase 1: Scrape categories")
        print("Phase 2: Match products")
        print("\nEstimated time: 20-25 minutes")
        print("\nStarting in 3 seconds...")
        time.sleep(3)
        
        # Load Tienda products
        self.load_tienda_products()
        
        # Start browser
        print("\n🌐 Starting browser...")
        self.driver = self.create_browser()
        print("   ✅ Browser ready")
        
        try:
            # Phase 1A: Scrape Disco
            self.scrape_disco_category(max_pages=3)
            
            # Phase 1B: Scrape Devoto
            self.scrape_devoto_category(max_pages=3)
            
            print("\n" + "="*80)
            print("PHASE 1 COMPLETE")
            print("="*80)
            print(f"Products scraped:")
            print(f"   • Tienda Inglesa: {len(self.tienda_products)}")
            print(f"   • Disco: {len(self.disco_products)}")
            print(f"   • Devoto: {len(self.devoto_products)}")
            print(f"   • Total: {len(self.tienda_products) + len(self.disco_products) + len(self.devoto_products)}")
            
            # Phase 2: Match products
            print("\n" + "="*80)
            print("PHASE 2: MATCHING")
            print("="*80)
            
            # Match by barcode (most accurate)
            barcode_matches = self.match_by_barcode()
            self.matches.extend(barcode_matches)
            
            # Match by name similarity
            name_matches = self.match_by_name_similarity(threshold=0.75)
            self.matches.extend(name_matches)
            
            print(f"\n✅ Total matches found: {len(self.matches)}")
            
            # Create reports
            self.create_comparison_report()
            self.save_all_products()
            
            print("\n" + "🎉"*40)
            print("HYBRID MATCHING COMPLETE!")
            print("🎉"*40)
            
            return self.matches
            
        finally:
            if self.driver:
                self.driver.quit()


def main():
    matcher = HybridMatcher()
    matches = matcher.run()
    
    print(f"\n✅ Found {len(matches)} total matches")
    print(f"📂 Check results/hybrid_comparison.csv for price comparisons")


if __name__ == "__main__":
    main()
