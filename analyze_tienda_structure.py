"""
Deep analysis of Tienda Inglesa website structure
- Analyze list pages
- Analyze product detail pages  
- Find correct selectors
- Extract barcodes
"""
import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup


def create_browser():
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


def analyze_search_page():
    """Analyze search results page structure"""
    print("\n" + "="*80)
    print("🔍 ANALYZING TIENDA INGLESA SEARCH PAGE")
    print("="*80)
    
    driver = create_browser()
    
    try:
        # Navigate
        print("\n1. Navigating to search page...")
        driver.get('https://www.tiendainglesa.com.uy/supermercado/buscar?texto=conaprole')
        time.sleep(5)
        
        # Scroll
        print("2. Scrolling to load content...")
        for i in range(3):
            driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(1)
        
        # Save HTML
        html = driver.page_source
        with open('results/tienda_search_page.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("   ✅ Saved to results/tienda_search_page.html")
        
        # Parse
        soup = BeautifulSoup(html, 'html.parser')
        
        # Analyze structure
        print("\n3. Analyzing page structure...")
        print("-" * 80)
        
        # Find all elements with 'product' in class name
        product_elements = soup.find_all(class_=lambda x: x and 'product' in x.lower())
        print(f"\n   Elements with 'product' in class: {len(product_elements)}")
        
        if product_elements:
            print("\n   Sample classes:")
            unique_classes = set()
            for elem in product_elements[:20]:
                classes = elem.get('class', [])
                for cls in classes:
                    if 'product' in cls.lower():
                        unique_classes.add(cls)
            
            for cls in sorted(unique_classes)[:10]:
                print(f"      • {cls}")
        
        # Find all elements with 'card' in class name
        card_elements = soup.find_all(class_=lambda x: x and 'card' in x.lower())
        print(f"\n   Elements with 'card' in class: {len(card_elements)}")
        
        if card_elements:
            print("\n   Sample classes:")
            unique_classes = set()
            for elem in card_elements[:20]:
                classes = elem.get('class', [])
                for cls in classes:
                    if 'card' in cls.lower():
                        unique_classes.add(cls)
            
            for cls in sorted(unique_classes)[:10]:
                print(f"      • {cls}")
        
        # Find links to products
        product_links = soup.find_all('a', href=lambda x: x and 'producto' in x)
        print(f"\n   Links to product pages: {len(product_links)}")
        
        if product_links:
            print("\n   Sample product URLs:")
            for link in product_links[:5]:
                href = link.get('href')
                text = link.get_text().strip()[:50]
                print(f"      • {text} → {href}")
        
        # Find price elements
        price_elements = soup.find_all(class_=lambda x: x and ('price' in x.lower() or 'precio' in x.lower()))
        print(f"\n   Elements with 'price' in class: {len(price_elements)}")
        
        if price_elements:
            print("\n   Sample prices:")
            for elem in price_elements[:5]:
                text = elem.get_text().strip()
                classes = elem.get('class', [])
                if text:
                    print(f"      • {text} (class: {classes})")
        
        # Try to find actual product containers
        print("\n4. Looking for actual product containers...")
        print("-" * 80)
        
        # Different possible selectors
        selectors = [
            '.card-product-container',
            '[class*="card-product"]',
            '[class*="product-card"]',
            'article',
            '[data-product]',
            '.product-item',
            '[class*="item-product"]'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                print(f"\n   ✅ '{selector}' found {len(elements)} elements")
                
                # Analyze first element
                first = elements[0]
                print(f"\n   Structure of first element:")
                print(f"      Tag: {first.name}")
                print(f"      Classes: {first.get('class', [])}")
                print(f"      ID: {first.get('id', 'none')}")
                
                # Find child elements
                name_elem = first.find(class_=lambda x: x and ('name' in x.lower() or 'title' in x.lower()))
                if name_elem:
                    print(f"      Name element found: {name_elem.get('class')}")
                    print(f"      Name text: {name_elem.get_text().strip()[:50]}")
                
                price_elem = first.find(class_=lambda x: x and 'price' in x.lower())
                if price_elem:
                    print(f"      Price element found: {price_elem.get('class')}")
                    print(f"      Price text: {price_elem.get_text().strip()}")
                
                img_elem = first.find('img')
                if img_elem:
                    print(f"      Image found: {img_elem.get('class')}")
                    print(f"      Image src: {img_elem.get('src', 'none')[:70]}")
                
                link_elem = first.find('a', href=True)
                if link_elem:
                    print(f"      Link found: {link_elem.get('href')[:70]}")
        
        print("\n" + "="*80)
        print("✅ Analysis complete! Check results/tienda_search_page.html")
        print("="*80)
        
        return driver
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        driver.quit()
        return None


def analyze_product_page(driver=None):
    """Analyze product detail page structure"""
    print("\n" + "="*80)
    print("📄 ANALYZING TIENDA INGLESA PRODUCT PAGE")
    print("="*80)
    
    close_driver = False
    if not driver:
        driver = create_browser()
        close_driver = True
    
    try:
        # Use a known product URL
        product_url = "https://www.tiendainglesa.com.uy/supermercado/queso-muzzarella-conaprole-kg.producto?1097368,,42"
        
        print(f"\n1. Navigating to product page...")
        print(f"   URL: {product_url}")
        driver.get(product_url)
        time.sleep(5)
        
        # Save HTML
        html = driver.page_source
        with open('results/tienda_product_page.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("   ✅ Saved to results/tienda_product_page.html")
        
        # Parse
        soup = BeautifulSoup(html, 'html.parser')
        
        print("\n2. Analyzing product page structure...")
        print("-" * 80)
        
        # Find product name
        print("\n   Looking for product name...")
        name_selectors = [
            'h1', 'h2', '.product-name', '.product-title',
            '[class*="product-name"]', '[class*="title"]'
        ]
        
        for selector in name_selectors:
            elem = soup.select_one(selector)
            if elem and elem.get_text().strip():
                print(f"      ✅ '{selector}': {elem.get_text().strip()[:60]}")
                print(f"         Classes: {elem.get('class', [])}")
        
        # Find price
        print("\n   Looking for price...")
        price_selectors = [
            '[class*="price"]', '[class*="Price"]', '[class*="precio"]',
            '.price', '.precio'
        ]
        
        for selector in price_selectors:
            elems = soup.select(selector)
            for elem in elems[:3]:
                text = elem.get_text().strip()
                if text and any(char.isdigit() for char in text):
                    print(f"      ✅ '{selector}': {text}")
                    print(f"         Classes: {elem.get('class', [])}")
        
        # Find barcode
        print("\n   Looking for barcode/EAN/SKU...")
        
        # Search in text
        text = soup.get_text()
        import re
        
        patterns = {
            'EAN': r'ean[:\s]+(\d{8,14})',
            'Código': r'código[:\s]+(\d{8,14})',
            'SKU': r'sku[:\s]+(\d{8,14})',
            'Código de barras': r'código de barras[:\s]+(\d{8,14})',
            '13-digit': r'\b(\d{13})\b',
            '12-digit': r'\b(\d{12})\b'
        }
        
        for name, pattern in patterns.items():
            matches = re.findall(pattern, text.lower())
            if matches:
                print(f"      ✅ {name}: {matches[:3]}")
        
        # Look for structured data (JSON-LD)
        print("\n   Looking for structured data...")
        scripts = soup.find_all('script', type='application/ld+json')
        if scripts:
            print(f"      Found {len(scripts)} JSON-LD scripts")
            for i, script in enumerate(scripts):
                try:
                    data = json.loads(script.string)
                    if 'gtin' in str(data) or 'sku' in str(data):
                        print(f"      ✅ Script {i+1} contains product identifiers:")
                        print(f"         {json.dumps(data, indent=8)[:500]}")
                except:
                    pass
        
        # Look for meta tags
        print("\n   Looking for meta tags...")
        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            name = meta.get('name', '') or meta.get('property', '')
            content = meta.get('content', '')
            if name and content and any(x in name.lower() for x in ['product', 'sku', 'ean', 'gtin']):
                print(f"      ✅ {name}: {content}")
        
        # Find images
        print("\n   Looking for product images...")
        img_selectors = [
            '.product-image', '[class*="product-img"]',
            '[class*="product-image"]', 'img[alt]'
        ]
        
        for selector in img_selectors:
            imgs = soup.select(selector)
            for img in imgs[:2]:
                src = img.get('src', '') or img.get('data-src', '')
                if src and 'product' in src.lower():
                    print(f"      ✅ '{selector}': {src[:70]}")
                    print(f"         Alt: {img.get('alt', 'none')}")
        
        # Find description
        print("\n   Looking for product description...")
        desc_selectors = [
            '.product-description', '[class*="description"]',
            '.product-details', '[class*="details"]'
        ]
        
        for selector in desc_selectors:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text().strip()[:200]
                if text:
                    print(f"      ✅ '{selector}': {text}...")
        
        print("\n" + "="*80)
        print("✅ Analysis complete! Check results/tienda_product_page.html")
        print("="*80)
        
        if close_driver:
            driver.quit()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        if close_driver:
            driver.quit()


def analyze_category_page():
    """Analyze category page structure (the one that works)"""
    print("\n" + "="*80)
    print("📂 ANALYZING TIENDA INGLESA CATEGORY PAGE (Working)")
    print("="*80)
    
    driver = create_browser()
    
    try:
        # Use the category URL that worked before
        category_url = "https://www.tiendainglesa.com.uy/supermercado/categoria/1/lacteos-huevos-y-refrigerados"
        
        print(f"\n1. Navigating to category page...")
        print(f"   URL: {category_url}")
        driver.get(category_url)
        time.sleep(5)
        
        # Scroll
        print("2. Scrolling to load content...")
        for i in range(3):
            driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(1)
        
        # Save HTML
        html = driver.page_source
        with open('results/tienda_category_page.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("   ✅ Saved to results/tienda_category_page.html")
        
        # Parse
        soup = BeautifulSoup(html, 'html.parser')
        
        print("\n3. Analyzing working category page structure...")
        print("-" * 80)
        
        # This is the selector that WORKS
        containers = soup.select('.card-product-container')
        print(f"\n   ✅ Found {len(containers)} .card-product-container elements")
        
        if containers:
            print("\n   Analyzing first container structure:")
            first = containers[0]
            
            # Name
            name_elem = first.select_one('.card-product-name')
            if name_elem:
                print(f"      ✅ Name: {name_elem.get_text().strip()}")
                print(f"         Selector: .card-product-name")
            
            # Price
            price_elem = first.select_one('.ProductPrice')
            if price_elem:
                print(f"      ✅ Price: {price_elem.get_text().strip()}")
                print(f"         Selector: .ProductPrice")
            
            # Image
            img_elem = first.select_one('.card-product-img')
            if img_elem:
                src = img_elem.get('src') or img_elem.get('data-src')
                print(f"      ✅ Image: {src[:70] if src else 'none'}")
                print(f"         Selector: .card-product-img")
            
            # Link
            link_elem = first.select_one('a[href*="producto"]')
            if link_elem:
                href = link_elem.get('href')
                print(f"      ✅ Link: {href[:70] if href else 'none'}")
                print(f"         Selector: a[href*='producto']")
            
            print(f"\n   Full HTML of first container:")
            print(f"{str(first)[:1000]}...")
        
        print("\n" + "="*80)
        print("✅ Analysis complete! This structure WORKS for category pages")
        print("="*80)
        
        return driver
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        driver.quit()
        return None


def main():
    """Run all analyses"""
    print("\n" + "🔬"*40)
    print("TIENDA INGLESA WEBSITE STRUCTURE ANALYSIS")
    print("🔬"*40)
    
    print("\nThis will analyze:")
    print("  1. Category page (working) - to understand what works")
    print("  2. Search page (not working) - to find correct selectors")
    print("  3. Product detail page - to extract barcodes")
    print("\nPress Ctrl+C to cancel or wait 5 seconds...")
    
    time.sleep(5)
    
    # Analyze category page first (working)
    driver = analyze_category_page()
    
    if driver:
        time.sleep(3)
        
        # Analyze search page  
        driver.quit()
        driver = analyze_search_page()
        
        if driver:
            time.sleep(3)
            
            # Analyze product detail page
            analyze_product_page(driver)
            
            driver.quit()
    
    print("\n" + "="*80)
    print("📊 ANALYSIS COMPLETE")
    print("="*80)
    print("\nHTML files saved to results/ directory:")
    print("  • tienda_category_page.html (working structure)")
    print("  • tienda_search_page.html (need to debug)")
    print("  • tienda_product_page.html (for barcode extraction)")
    print("\nReview these files to understand the structure!")
    print("="*80)


if __name__ == "__main__":
    main()
