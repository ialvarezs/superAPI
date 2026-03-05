"""
Final deep analysis using REAL Tienda Inglesa URLs
Understanding pagination and category structure
"""
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import json


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


def analyze_url(driver, url, name):
    """Analyze a specific URL"""
    print(f"\n{'='*80}")
    print(f"📄 ANALYZING: {name}")
    print(f"{'='*80}")
    print(f"URL: {url}\n")
    
    driver.get(url)
    time.sleep(5)
    
    # Scroll
    for _ in range(3):
        driver.execute_script("window.scrollBy(0, 500);")
        time.sleep(0.5)
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # Save HTML
    filename = f"results/{name.replace(' ', '_').lower()}.html"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    print(f"✅ Saved HTML to {filename}")
    
    # Analyze containers
    containers = soup.select('.card-product-container')
    print(f"\n📦 Found {len(containers)} .card-product-container elements")
    
    if containers:
        print("\n📋 First 5 products:")
        for i, container in enumerate(containers[:5], 1):
            name_elem = container.select_one('.card-product-name, .card-product-name-and-price')
            price_elem = container.select_one('.ProductPrice')
            link_elem = container.select_one('a[href*="producto"]')
            
            if name_elem:
                name_text = name_elem.get_text().strip()
                # Clean name (remove price if present)
                if '$' in name_text:
                    name_text = name_text.split('$')[0].strip()
                
                price_text = price_elem.get_text().strip() if price_elem else 'N/A'
                link = link_elem.get('href') if link_elem else 'N/A'
                
                print(f"\n  {i}. {name_text[:60]}")
                print(f"     Price: {price_text}")
                print(f"     Link: {link[:70] if link != 'N/A' else 'N/A'}")
    
    # Look for pagination
    print("\n🔢 Looking for pagination...")
    pagination = soup.select('[class*="pag"], [class*="next"], a[href*=",,"]')
    if pagination:
        print(f"   Found {len(pagination)} pagination elements")
        for elem in pagination[:5]:
            text = elem.get_text().strip()
            href = elem.get('href', '')
            if text or href:
                print(f"   • {text} → {href[:50]}")
    else:
        print("   No pagination found")
    
    # Look for category info
    print("\n📂 Looking for category structure...")
    category_elems = soup.select('[class*="category"], [class*="breadcrumb"]')
    if category_elems:
        print(f"   Found {len(category_elems)} category elements")
        for elem in category_elems[:3]:
            text = elem.get_text().strip()
            if text:
                print(f"   • {text[:80]}")


def analyze_product_page(driver, url, name):
    """Analyze product detail page"""
    print(f"\n{'='*80}")
    print(f"🔍 ANALYZING PRODUCT: {name}")
    print(f"{'='*80}")
    print(f"URL: {url}\n")
    
    driver.get(url)
    time.sleep(5)
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # Save HTML
    filename = f"results/product_{name.replace(' ', '_').lower()}.html"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    print(f"✅ Saved HTML to {filename}")
    
    # Product name
    h1 = soup.find('h1')
    if h1:
        print(f"\n📌 Product Name: {h1.get_text().strip()}")
    
    # Price
    price_elems = soup.select('[class*="Price"]')
    if price_elems:
        print(f"\n💰 Prices found:")
        for i, elem in enumerate(price_elems[:3], 1):
            text = elem.get_text().strip()
            if text and '$' in text:
                print(f"   {i}. {text}")
    
    # Barcode in JSON-LD
    print(f"\n🏷️  Looking for barcode...")
    scripts = soup.find_all('script', type='application/ld+json')
    barcode_found = False
    
    for script in scripts:
        try:
            data = json.loads(script.string)
            
            # Check for various barcode fields
            barcode = (data.get('gtin13') or data.get('gtin') or 
                      data.get('ean') or data.get('sku'))
            
            if barcode:
                print(f"   ✅ Found in JSON-LD: {barcode}")
                barcode_found = True
                print(f"\n   JSON-LD snippet:")
                print(f"   {json.dumps(data, indent=6)[:500]}...")
                break
        except:
            pass
    
    if not barcode_found:
        # Try text search
        import re
        text = soup.get_text()
        patterns = [
            (r'ean[:\s]+(\d{8,14})', 'EAN'),
            (r'gtin[:\s]+(\d{8,14})', 'GTIN'),
            (r'\b(\d{13})\b', '13-digit number')
        ]
        
        for pattern, name in patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                print(f"   ⚠️  Found in text ({name}): {matches[0]}")
                barcode_found = True
                break
    
    if not barcode_found:
        print(f"   ❌ No barcode found")
    
    # Brand
    print(f"\n🏢 Looking for brand...")
    brand_elem = soup.find('span', class_='brand') or soup.find(class_=lambda x: x and 'brand' in x.lower())
    if brand_elem:
        print(f"   ✅ Brand: {brand_elem.get_text().strip()}")
    else:
        # Check in JSON-LD
        for script in scripts:
            try:
                data = json.loads(script.string)
                if 'brand' in data:
                    brand = data['brand']
                    if isinstance(brand, dict):
                        print(f"   ✅ Brand (JSON-LD): {brand.get('name')}")
                    else:
                        print(f"   ✅ Brand (JSON-LD): {brand}")
            except:
                pass


def main():
    """Analyze all provided URLs"""
    print("\n" + "🔬"*40)
    print("FINAL TIENDA INGLESA URL ANALYSIS")
    print("Using REAL URLs from the site")
    print("🔬"*40)
    
    driver = create_browser()
    
    try:
        # 1. Main products URL
        analyze_url(
            driver,
            "https://www.tiendainglesa.com.uy/supermercado/busqueda?0,0,*%3A*,0,0,0,rel,,false,,,,0",
            "Main Products Page"
        )
        
        time.sleep(3)
        
        # 2. Almacen category
        analyze_url(
            driver,
            "https://www.tiendainglesa.com.uy/supermercado/categoria/almacen/busqueda?0,0,*%3A*,78,0,0,rel,,false,,,,0",
            "Almacen Category Page 1"
        )
        
        time.sleep(3)
        
        # 3. Almacen category page 2
        analyze_url(
            driver,
            "https://www.tiendainglesa.com.uy/supermercado/categoria/almacen/busqueda?0,0,*%3A*,78,0,0,rel,,false,,,,1",
            "Almacen Category Page 2"
        )
        
        time.sleep(3)
        
        # 4. Product 1
        analyze_product_page(
            driver,
            "https://www.tiendainglesa.com.uy/supermercado/harina-tipo-0000-tienda-inglesa-1-kg.producto?7398",
            "Harina Product"
        )
        
        time.sleep(3)
        
        # 5. Product 2
        analyze_product_page(
            driver,
            "https://www.tiendainglesa.com.uy/supermercado/galleta-oreo-sin-gluten-95-gr.producto?1579713",
            "Oreo Product"
        )
        
        print("\n" + "="*80)
        print("📊 ANALYSIS COMPLETE!")
        print("="*80)
        print("\nKey findings saved to results/ directory:")
        print("  • main_products_page.html")
        print("  • almacen_category_page_1.html")
        print("  • almacen_category_page_2.html")
        print("  • product_harina_product.html")
        print("  • product_oreo_product.html")
        
        print("\n💡 INSIGHTS:")
        print("=" * 80)
        print("1. URL Pattern for categories:")
        print("   /supermercado/categoria/[CATEGORY]/busqueda?0,0,*%3A*,[ID],0,0,rel,,false,,,,0")
        print("\n2. Pagination pattern:")
        print("   Last number in URL changes: ,,0 (page 1), ,,1 (page 2), ,,2 (page 3)")
        print("\n3. Product URL pattern:")
        print("   /supermercado/[PRODUCT-SLUG].producto?[ID]")
        print("\n4. To scrape more products:")
        print("   • Find category IDs (like 78 for 'almacen')")
        print("   • Use pagination: increment last number")
        print("   • Extract product links from each page")
        print("   • Visit product pages for barcodes")
        
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
