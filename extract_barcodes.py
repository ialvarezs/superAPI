"""
Barcode Extractor for Disco & Devoto products
Extract barcodes from product pages to enable perfect matching
"""
import time
import random
import json
import re
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from difflib import SequenceMatcher
import pandas as pd


class BarcodeExtractor:
    """Extract barcodes from Disco & Devoto product pages"""
    
    def __init__(self):
        self.driver = None
    
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
    
    def human_delay(self, min_sec: float = 0.5, max_sec: float = 1.5):
        """Random human-like delay"""
        time.sleep(random.uniform(min_sec, max_sec))
    
    def extract_barcode_from_page(self, url: str) -> Optional[str]:
        """Extract barcode from product page"""
        try:
            self.driver.get(url)
            self.human_delay(1, 2)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Method 1: Look for JSON-LD structured data
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    barcode = data.get('gtin13') or data.get('gtin') or data.get('ean') or data.get('sku')
                    if barcode and str(barcode).isdigit() and len(str(barcode)) >= 8:
                        return str(barcode)
                except:
                    pass
            
            # Method 2: Look for data attributes
            barcode_elem = soup.find(attrs={'data-barcode': True}) or soup.find(attrs={'data-ean': True})
            if barcode_elem:
                barcode = barcode_elem.get('data-barcode') or barcode_elem.get('data-ean')
                if barcode and str(barcode).isdigit():
                    return str(barcode)
            
            # Method 3: Search in page text
            text = soup.get_text()
            patterns = [
                r'ean[:\s]+(\d{8,14})',
                r'gtin[:\s]+(\d{8,14})',
                r'código[:\s]+(\d{8,14})',
                r'\b(\d{13})\b',  # 13-digit EAN
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text.lower())
                if matches:
                    return matches[0]
            
            return None
            
        except Exception as e:
            return None
    
    def extract_barcodes_for_products(self, products: list):
        """Extract barcodes for a list of products"""
        total = len(products)
        found = 0
        
        for i, product in enumerate(products, 1):
            if i % 10 == 0:
                print(f"   Progress: {i}/{total} ({i*100//total}%) - Found: {found} barcodes")
            
            url = product.get('url')
            if not url:
                continue
            
            barcode = self.extract_barcode_from_page(url)
            if barcode:
                product['barcode'] = barcode
                found += 1
            
            # Small delay
            self.human_delay(0.5, 1)
        
        return found
    
    def run(self):
        """Run barcode extraction"""
        print("\n" + "🏷️"*40)
        print("BARCODE EXTRACTOR")
        print("🏷️"*40)
        
        # Load products
        print("\n📦 Loading products...")
        with open('data/all_products_hybrid.json', 'r', encoding='utf-8') as f:
            all_products = json.load(f)
        
        disco_products = [p for p in all_products if p['supermarket'] == 'Disco']
        devoto_products = [p for p in all_products if p['supermarket'] == 'Devoto']
        tienda_products = [p for p in all_products if p['supermarket'] == 'Tienda Inglesa']
        
        print(f"   ✅ Disco: {len(disco_products)} products")
        print(f"   ✅ Devoto: {len(devoto_products)} products")
        print(f"   ✅ Tienda: {len(tienda_products)} products (already have barcodes)")
        
        print(f"\n⏱️  Estimated time: {(len(disco_products) + len(devoto_products)) * 1.5 / 60:.1f} minutes")
        print("\nStarting in 3 seconds...")
        time.sleep(3)
        
        # Start browser
        print("\n🌐 Starting browser...")
        self.driver = self.create_browser()
        print("   ✅ Browser ready")
        
        try:
            # Extract Disco barcodes
            print(f"\n🛒 EXTRACTING BARCODES: Disco ({len(disco_products)} products)")
            print("="*80)
            disco_found = self.extract_barcodes_for_products(disco_products)
            print(f"\n✅ Disco: {disco_found}/{len(disco_products)} barcodes found ({disco_found*100//len(disco_products) if disco_products else 0}%)")
            
            # Extract Devoto barcodes
            print(f"\n🛒 EXTRACTING BARCODES: Devoto ({len(devoto_products)} products)")
            print("="*80)
            devoto_found = self.extract_barcodes_for_products(devoto_products)
            print(f"\n✅ Devoto: {devoto_found}/{len(devoto_products)} barcodes found ({devoto_found*100//len(devoto_products) if devoto_products else 0}%)")
            
            # Save updated products
            print("\n💾 Saving updated products...")
            updated_products = tienda_products + disco_products + devoto_products
            
            with open('data/all_products_with_barcodes.json', 'w', encoding='utf-8') as f:
                json.dump(updated_products, f, ensure_ascii=False, indent=2)
            
            print(f"   ✅ Saved: data/all_products_with_barcodes.json")
            
            # Now match by barcodes
            print("\n🔗 MATCHING PRODUCTS BY BARCODE...")
            print("="*80)
            
            matches = self.match_by_barcode(tienda_products, disco_products + devoto_products)
            
            print(f"\n✅ Found {len(matches)} barcode matches!")
            
            # Create comparison report
            self.create_comparison_report(matches)
            
            # Save matches
            with open('results/final_barcode_matches.json', 'w', encoding='utf-8') as f:
                json.dump(matches, f, ensure_ascii=False, indent=2)
            
            print(f"   ✅ Saved: results/final_barcode_matches.json")
            
            print("\n" + "🎉"*40)
            print("BARCODE EXTRACTION COMPLETE!")
            print("🎉"*40)
            
            return matches
            
        finally:
            if self.driver:
                self.driver.quit()
    
    def match_by_barcode(self, tienda_products: list, other_products: list):
        """Match products using barcodes"""
        matches = []
        
        # Create barcode lookup
        barcode_lookup = {}
        for prod in other_products:
            barcode = prod.get('barcode')
            if barcode:
                if barcode not in barcode_lookup:
                    barcode_lookup[barcode] = []
                barcode_lookup[barcode].append(prod)
        
        print(f"   Barcode index: {len(barcode_lookup)} unique barcodes")
        
        for tienda_prod in tienda_products:
            barcode = tienda_prod.get('barcode')
            if not barcode:
                continue
            
            matched = barcode_lookup.get(barcode, [])
            
            if matched:
                match_group = {
                    'barcode': barcode,
                    'tienda_product': tienda_prod,
                    'matched_products': matched
                }
                matches.append(match_group)
        
        return matches
    
    def create_comparison_report(self, matches: list):
        """Create price comparison report"""
        print("\n📊 CREATING COMPARISON REPORT...")
        print("="*80)
        
        comparison_data = []
        
        for match in matches:
            tienda = match['tienda_product']
            
            for other in match['matched_products']:
                t_price = tienda.get('price')
                o_price = other.get('price')
                
                if t_price and o_price:
                    diff = o_price - t_price
                    pct = (abs(diff) / t_price) * 100
                    cheaper = 'Tienda Inglesa' if t_price < o_price else other['supermarket']
                    
                    comparison_data.append({
                        'Barcode': match['barcode'],
                        'Product_Tienda': tienda['name'][:60],
                        'Product_Other': other['name'][:60],
                        'Store': other['supermarket'],
                        'Price_Tienda': f"${t_price:.0f}",
                        'Price_Other': f"${o_price:.0f}",
                        'Difference': f"${abs(diff):.0f}",
                        'Percentage': f"{pct:.1f}%",
                        'Cheaper_At': cheaper,
                        'Savings': abs(diff) if t_price < o_price else -abs(diff)
                    })
        
        if comparison_data:
            df = pd.DataFrame(comparison_data)
            df.to_csv('results/final_price_comparison.csv', index=False, encoding='utf-8')
            
            print(f"   ✅ Saved: results/final_price_comparison.csv")
            print(f"\n📊 STATISTICS:")
            print(f"   • Total matches: {len(matches)}")
            print(f"   • Price comparisons: {len(comparison_data)}")
            
            # Calculate savings
            tienda_cheaper = sum(1 for row in comparison_data if row['Cheaper_At'] == 'Tienda Inglesa')
            others_cheaper = len(comparison_data) - tienda_cheaper
            
            print(f"   • Tienda Inglesa cheaper: {tienda_cheaper} ({tienda_cheaper*100//len(comparison_data)}%)")
            print(f"   • Others cheaper: {others_cheaper} ({others_cheaper*100//len(comparison_data)}%)")
            
            # Top 10 best deals at Tienda
            df_sorted = df.sort_values('Savings', ascending=False)
            print(f"\n💰 TOP 10 BEST DEALS AT TIENDA INGLESA:")
            print("-"*80)
            for idx, row in df_sorted.head(10).iterrows():
                if row['Cheaper_At'] == 'Tienda Inglesa':
                    print(f"\n{list(df_sorted.head(10).index).index(idx)+1}. {row['Product_Tienda']}")
                    print(f"   Tienda: {row['Price_Tienda']} vs {row['Store']}: {row['Price_Other']}")
                    print(f"   💰 Save: {row['Difference']} ({row['Percentage']})")
        else:
            print("   ⚠️  No price comparisons available")


def main():
    extractor = BarcodeExtractor()
    matches = extractor.run()
    
    print(f"\n✅ Extraction complete!")
    print(f"📊 {len(matches)} products matched across supermarkets")
    print(f"📂 Check results/final_price_comparison.csv")


if __name__ == "__main__":
    main()
