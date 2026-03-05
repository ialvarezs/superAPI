"""
Advanced anti-bot scraper for Tienda Inglesa with multiple evasion techniques
"""
import time
import random
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import json
from typing import List, Dict, Optional
import undetected_chromedriver as uc


class StealthScraper:
    def __init__(self):
        # Realistic user agents from different browsers and devices
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]

        # Common headers to look more human
        self.headers_base = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-UY,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }

        self.session = None
        self.driver = None

    def get_random_headers(self) -> Dict[str, str]:
        """Generate randomized headers"""
        headers = self.headers_base.copy()
        headers['User-Agent'] = random.choice(self.user_agents)
        return headers

    def create_stealth_session(self) -> requests.Session:
        """Create a requests session with stealth features"""
        session = requests.Session()
        session.headers.update(self.get_random_headers())

        # Add some cookies to look more legitimate
        session.cookies.set('lang', 'es')
        session.cookies.set('currency', 'UYU')

        return session

    def create_undetected_browser(self) -> webdriver.Chrome:
        """Create an undetected Chrome browser"""
        try:
            options = uc.ChromeOptions()

            # Basic stealth options
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-plugins')
            options.add_argument('--disable-images')  # Faster loading
            options.add_argument('--disable-javascript')  # Try without JS first

            # Randomize window size
            width = random.randint(1200, 1920)
            height = random.randint(800, 1080)
            options.add_argument(f'--window-size={width},{height}')

            # Random user agent
            options.add_argument(f'--user-agent={random.choice(self.user_agents)}')

            # Language preferences
            options.add_argument('--lang=es-UY')

            driver = uc.Chrome(options=options)

            # Execute stealth scripts
            stealth_js = """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });

            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });

            Object.defineProperty(navigator, 'languages', {
                get: () => ['es-UY', 'es', 'en'],
            });

            window.chrome = {
                runtime: {},
            };
            """
            driver.execute_script(stealth_js)

            return driver

        except Exception as e:
            print(f"Failed to create undetected browser: {e}")
            # Fallback to regular Chrome
            return self.create_regular_browser()

    def create_regular_browser(self) -> webdriver.Chrome:
        """Fallback: Create regular Chrome with stealth options"""
        options = Options()

        # Comprehensive stealth options
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-automation')
        options.add_argument('--disable-web-security')
        options.add_argument('--allow-running-insecure-content')
        options.add_argument('--disable-features=VizDisplayCompositor')

        # Randomize
        width = random.randint(1200, 1920)
        height = random.randint(800, 1080)
        options.add_argument(f'--window-size={width},{height}')
        options.add_argument(f'--user-agent={random.choice(self.user_agents)}')

        # Language
        options.add_argument('--lang=es-UY')
        options.add_experimental_option('prefs', {'intl.accept_languages': 'es-UY,es,en'})

        # Exclude automation switches
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        # Set Chrome binary path
        options.binary_location = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        # Execute stealth script
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        return driver

    def human_delay(self, min_seconds: float = 1, max_seconds: float = 3):
        """Simulate human-like delays"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)

    def try_requests_approach(self, url: str) -> Optional[BeautifulSoup]:
        """Try simple requests approach first"""
        print(f"🌐 Trying requests approach for {url}")

        try:
            session = self.create_stealth_session()

            # Add a delay
            self.human_delay(1, 2)

            response = session.get(url, timeout=30)

            print(f"Status code: {response.status_code}")

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                print("✅ Requests approach successful")
                return soup
            else:
                print(f"❌ Requests failed with status {response.status_code}")
                return None

        except Exception as e:
            print(f"❌ Requests approach failed: {e}")
            return None

    def try_selenium_approach(self, url: str) -> Optional[str]:
        """Try Selenium approach with stealth features"""
        print(f"🤖 Trying Selenium approach for {url}")

        try:
            # Try undetected Chrome first
            self.driver = self.create_undetected_browser()

            print("Browser created, navigating...")

            # Navigate with human-like behavior
            self.driver.get('https://www.google.com')  # Visit Google first (more human-like)
            self.human_delay(2, 4)

            # Now go to target site
            self.driver.get(url)
            self.human_delay(3, 6)

            print(f"Page title: {self.driver.title}")
            print(f"Current URL: {self.driver.current_url}")

            # Check if we got blocked
            page_source = self.driver.page_source.lower()

            blocked_indicators = [
                'access denied', 'blocked', 'forbidden', 'cloudflare',
                'security check', 'captcha', 'bot detection'
            ]

            if any(indicator in page_source for indicator in blocked_indicators):
                print("❌ Detected blocking/captcha page")
                return None

            if len(page_source) < 1000:
                print("❌ Page content too short, likely blocked")
                return None

            print("✅ Selenium approach successful")
            return self.driver.page_source

        except Exception as e:
            print(f"❌ Selenium approach failed: {e}")
            return None

        finally:
            if self.driver:
                self.driver.quit()

    def find_lacteos_urls(self, page_source: str, base_url: str) -> List[str]:
        """Find dairy/lacteos related URLs in page source"""
        soup = BeautifulSoup(page_source, 'html.parser')

        dairy_terms = [
            'lacteos', 'lácteos', 'lacteo', 'lácteo',
            'leche', 'dairy', 'milk', 'yogur', 'yogurt',
            'queso', 'cheese', 'manteca', 'butter'
        ]

        found_urls = set()

        # Look for links with dairy terms
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text().lower()

            # Check if link text contains dairy terms
            if any(term in text for term in dairy_terms):
                if href.startswith('http'):
                    found_urls.add(href)
                elif href.startswith('/'):
                    found_urls.add(base_url.rstrip('/') + href)

            # Check href for dairy terms
            if any(term in href.lower() for term in dairy_terms):
                if href.startswith('http'):
                    found_urls.add(href)
                elif href.startswith('/'):
                    found_urls.add(base_url.rstrip('/') + href)

        return list(found_urls)

    def scrape_tienda_inglesa(self) -> Dict:
        """Main method to scrape Tienda Inglesa"""
        base_url = 'https://www.tiendainglesa.com.uy'

        results = {
            'success': False,
            'method_used': None,
            'lacteos_urls': [],
            'products': [],
            'error': None
        }

        try:
            # Strategy 1: Try requests first
            soup = self.try_requests_approach(base_url)

            if soup:
                results['method_used'] = 'requests'
                page_source = str(soup)
            else:
                # Strategy 2: Try Selenium
                page_source = self.try_selenium_approach(base_url)

                if page_source:
                    results['method_used'] = 'selenium'
                else:
                    results['error'] = 'Both requests and selenium failed'
                    return results

            # Look for lacteos URLs
            lacteos_urls = self.find_lacteos_urls(page_source, base_url)
            results['lacteos_urls'] = lacteos_urls

            print(f"Found {len(lacteos_urls)} potential lacteos URLs:")
            for url in lacteos_urls[:5]:  # Show first 5
                print(f"  • {url}")

            # Try to scrape one of the lacteos URLs if found
            if lacteos_urls:
                test_url = lacteos_urls[0]
                print(f"\n🎯 Trying to scrape products from: {test_url}")

                # Try the same approach that worked for the main page
                if results['method_used'] == 'requests':
                    product_soup = self.try_requests_approach(test_url)
                    if product_soup:
                        products = self.extract_products_from_soup(product_soup, base_url)
                        results['products'] = products
                else:
                    product_page = self.try_selenium_approach(test_url)
                    if product_page:
                        product_soup = BeautifulSoup(product_page, 'html.parser')
                        products = self.extract_products_from_soup(product_soup, base_url)
                        results['products'] = products

            results['success'] = True

        except Exception as e:
            results['error'] = str(e)
            print(f"❌ Error scraping Tienda Inglesa: {e}")

        return results

    def extract_products_from_soup(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """Extract product information from BeautifulSoup object"""
        products = []

        # Common product container selectors
        product_selectors = [
            '.product-item', '.product', '.item', '.card',
            '.product-card', '.grid-item', '[data-product]',
            '.producto', '.articulo', '.item-product'
        ]

        product_elements = []
        for selector in product_selectors:
            elements = soup.select(selector)
            if elements:
                product_elements = elements
                print(f"Found {len(elements)} products using selector: {selector}")
                break

        for element in product_elements[:20]:  # Limit to first 20
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

                # Extract name
                name_selectors = ['.product-title', '.title', '.name', '.product-name', 'h1', 'h2', 'h3', 'h4']
                for selector in name_selectors:
                    name_elem = element.select_one(selector)
                    if name_elem and name_elem.get_text().strip():
                        product['name'] = name_elem.get_text().strip()
                        break

                # Extract price
                price_selectors = ['.price', '.precio', '.cost', '[class*="price"]', '.amount']
                for selector in price_selectors:
                    price_elem = element.select_one(selector)
                    if price_elem and price_elem.get_text().strip():
                        price_text = price_elem.get_text().strip()
                        product['original_price'] = price_text
                        # Try to extract numeric price
                        import re
                        price_match = re.search(r'[\d.,]+', price_text.replace('$', '').replace(',', '.'))
                        if price_match:
                            try:
                                product['price'] = float(price_match.group())
                            except:
                                pass
                        break

                # Extract image
                img = element.select_one('img')
                if img:
                    src = img.get('src') or img.get('data-src')
                    if src:
                        if src.startswith('http'):
                            product['image_url'] = src
                        elif src.startswith('/'):
                            product['image_url'] = base_url.rstrip('/') + src

                # Extract link
                link = element.select_one('a')
                if link:
                    href = link.get('href')
                    if href:
                        if href.startswith('http'):
                            product['url'] = href
                        elif href.startswith('/'):
                            product['url'] = base_url.rstrip('/') + href

                if product['name']:
                    products.append(product)

            except Exception as e:
                print(f"Error extracting product: {e}")
                continue

        return products


def main():
    print("🕵️ ADVANCED ANTI-BOT SCRAPING - TIENDA INGLESA")
    print("=" * 60)

    scraper = StealthScraper()
    results = scraper.scrape_tienda_inglesa()

    print(f"\n📊 RESULTS")
    print("-" * 20)
    print(f"Success: {results['success']}")
    print(f"Method used: {results['method_used']}")
    print(f"Lacteos URLs found: {len(results['lacteos_urls'])}")
    print(f"Products extracted: {len(results['products'])}")

    if results['error']:
        print(f"Error: {results['error']}")

    # Save results
    with open('results/tienda_inglesa_stealth_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Results saved to results/tienda_inglesa_stealth_results.json")

    if results['products']:
        print(f"\n🛒 SAMPLE PRODUCTS:")
        for product in results['products'][:3]:
            print(f"  • {product['name']} - ${product['price']}")


if __name__ == "__main__":
    main()