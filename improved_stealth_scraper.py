"""
Improved stealth scraper with better success detection and multiple fallback strategies
"""
import time
import random
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import json
import re


def create_stealth_browser():
    """Create a stealthy Chrome browser"""
    options = Options()

    # Basic stealth options
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-automation')
    options.add_argument('--disable-plugins')

    # Use a common user agent
    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    options.add_argument(f'--user-agent={user_agent}')

    # Window size
    options.add_argument('--window-size=1400,900')

    # Language
    options.add_argument('--lang=es-UY')

    # Disable automation indicators
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    # Set Chrome path
    options.binary_location = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    # Execute stealth script
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    return driver


def analyze_tienda_inglesa_page():
    """Analyze what we can actually access from Tienda Inglesa"""
    print("🔍 ANALYZING TIENDA INGLESA PAGE STRUCTURE")
    print("=" * 50)

    driver = None
    try:
        driver = create_stealth_browser()

        # Navigate step by step
        print("1. Going to Google first...")
        driver.get('https://www.google.com')
        time.sleep(2)

        print("2. Navigating to Tienda Inglesa...")
        driver.get('https://www.tiendainglesa.com.uy')
        time.sleep(5)

        print(f"Page title: {driver.title}")
        print(f"Current URL: {driver.current_url}")

        # Get page source
        page_source = driver.page_source

        print(f"Page source length: {len(page_source)} characters")

        # Save the full page source for inspection
        with open('results/tienda_inglesa_page_source.html', 'w', encoding='utf-8') as f:
            f.write(page_source)

        # Analyze the page
        soup = BeautifulSoup(page_source, 'html.parser')

        # Look for navigation elements
        print("\n🧭 NAVIGATION ANALYSIS:")
        nav_elements = soup.find_all(['nav', 'menu', 'ul'])
        print(f"Found {len(nav_elements)} navigation elements")

        # Look for links with potential dairy terms
        all_links = soup.find_all('a', href=True)
        print(f"Found {len(all_links)} total links")

        dairy_terms = ['lacteos', 'lácteos', 'leche', 'yogur', 'queso', 'manteca']
        dairy_links = []

        for link in all_links:
            href = link.get('href', '')
            text = link.get_text().lower()

            if any(term in text or term in href.lower() for term in dairy_terms):
                dairy_links.append({
                    'text': text.strip(),
                    'href': href,
                    'full_url': href if href.startswith('http') else f"https://www.tiendainglesa.com.uy{href}"
                })

        print(f"\n🥛 DAIRY-RELATED LINKS FOUND: {len(dairy_links)}")
        for link in dairy_links[:10]:  # Show first 10
            print(f"  • '{link['text']}' → {link['full_url']}")

        # Look for category structure
        print(f"\n📂 LOOKING FOR CATEGORY STRUCTURE:")

        # Try different approaches to find categories
        category_indicators = [
            'categoria', 'category', 'seccion', 'section',
            'departamento', 'department', 'producto', 'product'
        ]

        for indicator in category_indicators:
            elements = soup.find_all(attrs={"class": re.compile(indicator, re.I)})
            elements.extend(soup.find_all(attrs={"id": re.compile(indicator, re.I)}))

            if elements:
                print(f"  Found {len(elements)} elements with '{indicator}' in class/id")

        # Look for any product listings
        product_indicators = [
            'product-item', 'product', 'item', 'card',
            'producto', 'articulo', 'listing'
        ]

        for indicator in product_indicators:
            elements = soup.find_all(attrs={"class": re.compile(indicator, re.I)})

            if elements:
                print(f"  Found {len(elements)} potential product elements with '{indicator}'")

        # Check for JavaScript-heavy content
        scripts = soup.find_all('script')
        print(f"\n⚡ Found {len(scripts)} script tags (indicates JS-heavy site)")

        # Look for specific Tienda Inglesa patterns
        print(f"\n🏪 TIENDA INGLESA SPECIFIC PATTERNS:")

        # Check for common ecommerce platforms
        if 'shopify' in page_source.lower():
            print("  • Detected Shopify platform")
        if 'magento' in page_source.lower():
            print("  • Detected Magento platform")
        if 'woocommerce' in page_source.lower():
            print("  • Detected WooCommerce platform")

        # Try to find the main content area
        main_content = soup.find('main') or soup.find(id='main') or soup.find(class_=re.compile('main', re.I))
        if main_content:
            print("  • Found main content area")

        # Save results
        results = {
            'page_title': driver.title,
            'current_url': driver.current_url,
            'total_links': len(all_links),
            'dairy_links': dairy_links,
            'page_source_length': len(page_source),
            'script_tags': len(scripts)
        }

        with open('results/tienda_inglesa_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"\n💾 Full analysis saved to:")
        print(f"  • results/tienda_inglesa_page_source.html")
        print(f"  • results/tienda_inglesa_analysis.json")

        # If we found dairy links, try to access one
        if dairy_links:
            print(f"\n🎯 TESTING DAIRY LINK ACCESS:")
            test_link = dairy_links[0]
            print(f"Trying to access: {test_link['full_url']}")

            try:
                driver.get(test_link['full_url'])
                time.sleep(3)

                print(f"New page title: {driver.title}")
                print(f"New URL: {driver.current_url}")

                # Quick product count
                new_page = driver.page_source
                new_soup = BeautifulSoup(new_page, 'html.parser')

                for indicator in product_indicators:
                    elements = new_soup.find_all(attrs={"class": re.compile(indicator, re.I)})
                    if elements:
                        print(f"  Found {len(elements)} potential products on dairy page")

                        # Save this page too
                        with open('results/tienda_inglesa_dairy_page.html', 'w', encoding='utf-8') as f:
                            f.write(new_page)

                        print(f"  Dairy page saved to results/tienda_inglesa_dairy_page.html")
                        break

            except Exception as e:
                print(f"  ❌ Error accessing dairy link: {e}")

    except Exception as e:
        print(f"❌ Error during analysis: {e}")

    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    analyze_tienda_inglesa_page()