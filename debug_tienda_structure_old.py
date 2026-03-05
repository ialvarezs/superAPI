"""
Debug and analyze the actual HTML structure of Tienda Inglesa product pages
"""
import time
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


def analyze_search_page():
    """Analyze the actual structure of search results"""
    driver = None

    try:
        driver = create_stealth_browser()

        # Navigate to Tienda Inglesa
        print("Navigating to Tienda Inglesa...")
        driver.get('https://www.google.com')
        time.sleep(2)
        driver.get('https://www.tiendainglesa.com.uy')
        time.sleep(5)

        # Search for "leche"
        search_url = "https://www.tiendainglesa.com.uy/supermercado/buscar?texto=leche"
        print(f"Searching for 'leche'...")
        driver.get(search_url)
        time.sleep(5)

        # Scroll to load products
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Save the full page
        with open('results/tienda_inglesa_leche_search.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)

        print(f"✅ Full search page saved to results/tienda_inglesa_leche_search.html")

        # Find product elements
        products = soup.select('[class*="product"]')
        print(f"Found {len(products)} product-like elements")

        # Analyze first few products in detail
        for i, product in enumerate(products[:5]):
            print(f"\n--- PRODUCT {i+1} ---")
            print(f"HTML snippet: {str(product)[:200]}...")

            # Try to find text content
            text_content = product.get_text().strip()
            if text_content:
                print(f"Text content: {text_content[:100]}...")

            # Look for links
            links = product.find_all('a')
            if links:
                print(f"Links found: {len(links)}")
                for link in links[:2]:
                    href = link.get('href', '')
                    text = link.get_text().strip()
                    print(f"  Link: '{text[:50]}...' → {href[:50]}...")

            # Look for images
            images = product.find_all('img')
            if images:
                print(f"Images found: {len(images)}")
                for img in images[:1]:
                    src = img.get('src', '')
                    alt = img.get('alt', '')
                    print(f"  Image: alt='{alt[:30]}...' src='{src[:50]}...'")

            # Save individual product HTML
            with open(f'results/product_{i+1}.html', 'w', encoding='utf-8') as f:
                f.write(str(product))

            print(f"  Individual product HTML saved to results/product_{i+1}.html")

        # Try different product selectors
        print(f"\n--- TESTING DIFFERENT SELECTORS ---")
        selectors_to_try = [
            '.product-item',
            '.product-card',
            '.product',
            '[data-product]',
            '.card',
            '.item',
            'article',
            '[class*="prod"]',
            '[id*="product"]'
        ]

        for selector in selectors_to_try:
            elements = soup.select(selector)
            if elements:
                print(f"  {selector}: {len(elements)} elements")
                first_elem = elements[0]
                text = first_elem.get_text().strip()[:50]
                print(f"    First element text: '{text}...'")

        # Look for specific text patterns
        print(f"\n--- LOOKING FOR DAIRY PRODUCTS ---")
        page_text = soup.get_text().lower()

        dairy_terms = ['leche', 'conaprole', 'parmalat', 'yogur', 'queso']
        for term in dairy_terms:
            count = page_text.count(term)
            print(f"  '{term}' appears {count} times in page text")

        # Try to find actual product names in the HTML
        print(f"\n--- SEARCHING FOR PRODUCT NAME PATTERNS ---")

        # Look for common product name patterns
        import re

        # Pattern: Brand + product type + size
        patterns = [
            r'[A-Z][a-z]+ (?:leche|yogur|queso|manteca) \d+',
            r'(?:CONAPROLE|PARMALAT|CALCAR) [A-Za-z ]+',
            r'Leche [A-Za-z ]+ \d+[mlgL]',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, driver.page_source, re.IGNORECASE)
            if matches:
                print(f"  Pattern '{pattern}' found {len(matches)} matches:")
                for match in matches[:3]:
                    print(f"    - {match}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    print("🔬 DEBUGGING TIENDA INGLESA PRODUCT STRUCTURE")
    print("=" * 60)
    analyze_search_page()