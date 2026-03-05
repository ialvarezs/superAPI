"""
Enhanced Tienda Inglesa scraper for arroz category with EAN extraction
Uses Selenium for anti-bot protection
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import re
import time
import random
from typing import List, Dict, Optional
from logger import setup_logger

logger = setup_logger('tienda_inglesa_scraper')

class TiendaInglesaScraper:
    """Scraper for Tienda Inglesa supermarket with anti-blocking strategies using Selenium"""
    
    def __init__(self, base_url: str, category_url: str, headers: Dict = None):
        self.supermarket = "tienda_inglesa"
        self.base_url = base_url
        self.category_url = category_url
        self.driver = None
    
    def create_stealth_browser(self):
        """Create a stealth browser instance"""
        options = Options()
        
        # Stealth options - NOT headless so we can see it working
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
    
    def scrape_category(self, max_pages: int = 20, max_products: int = 30) -> List[Dict]:
        """Scrape arroz category from Tienda Inglesa - with product detail visits for EAN"""
        logger.info(f"Starting Tienda Inglesa scrape: {self.category_url}")
        
        products = []
        product_urls = []
        
        try:
            # Initial delay to appear human
            time.sleep(random.uniform(2, 4))
            
            # Rotate headers before category request
            self._update_session_headers()
            
            response = self.session.get(self.category_url, timeout=30)
            response.raise_for_status()
            
            # Ensure proper encoding
            if response.encoding is None or response.encoding == 'ISO-8859-1':
                response.encoding = 'utf-8'
            
            logger.info(f"Response status: {response.status_code}, Length: {len(response.text)}, Encoding: {response.encoding}")
            
            # Debug: Check if HTML contains producto and sample content
            if 'producto?' in response.text:
                logger.info(f"✓ HTML contains 'producto?' ({response.text.count('producto?')} times)")
            else:
                logger.warning("✗ HTML does not contain 'producto?'")
                # Log first 1000 chars to see what we got
                logger.warning(f"First 1000 chars of response: {response.text[:1000]}")
                # Check if we got a block page
                if 'robot' in response.text.lower() or 'captcha' in response.text.lower() or 'blocked' in response.text.lower():
                    logger.error("⚠️ DETECTED BLOCKING PAGE - Need to adjust strategy")
                    return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find product cards - Tienda Inglesa uses card-product-container class
            # Also look for links with /producto? pattern
            product_items = soup.find_all(['div'], class_=re.compile(r'card-product-container', re.I))
            
            # First try: Look for all links with 'producto' in href
            all_links = soup.find_all('a', href=re.compile(r'producto', re.I))
            logger.info(f"Found {len(all_links)} product links via href pattern")
            
            if all_links:
                
                for link in all_links:
                    href = link.get('href')
                    url = href if href.startswith('http') else self.base_url + href
                    link_text = link.get_text().lower()
                    
                    # Filter by arroz
                    if 'arroz' in link_text or 'arroz' in url.lower():
                        if url not in product_urls:
                            product_urls.append(url)
            else:
                logger.info(f"Found {len(product_items)} product card containers")
                
                for item in product_items:
                    link = item.find('a', href=True)
                    if link:
                        href = link.get('href')
                        url = href if href.startswith('http') else self.base_url + href
                        
                        # Filter by arroz in link text
                        if 'arroz' in link.get_text().lower() or 'arroz' in url.lower():
                            if url not in product_urls:
                                product_urls.append(url)
            
            logger.info(f"Found {len(product_urls)} arroz product URLs")
            
            # Visit product detail pages with human-like delays
            for i, url in enumerate(product_urls[:max_products], 1):
                try:
                    # Longer random delay between 12-25 seconds (more human-like)
                    if i > 1:
                        delay = random.uniform(12, 25)
                        logger.info(f"Waiting {delay:.1f}s before next request...")
                        time.sleep(delay)
                    
                    # Rotate user agent every few requests
                    if i % 3 == 0:
                        self._update_session_headers()
                        logger.debug("Rotated user agent")
                    
                    logger.info(f"Fetching product {i}/{min(len(product_urls), max_products)}: {url[:80]}...")
                    product = self._scrape_product_detail(url)
                    
                    if product:
                        products.append(product)
                        if product.get('ean'):
                            logger.info(f"✓ Product with EAN: {product['name'][:50]} - {product['ean']}")
                    else:
                        # If blocked, take a longer break
                        logger.warning("Product returned None, taking extended break...")
                        time.sleep(random.uniform(30, 45))
                        # Try refreshing session
                        self.session = requests.Session()
                        self._update_session_headers()
                    
                except Exception as e:
                    logger.error(f"Error fetching product: {e}")
                    # Long pause on error (might be getting blocked)
                    time.sleep(random.uniform(35, 50))
                    # Recreate session on error
                    self.session = requests.Session()
                    self._update_session_headers()
                    continue
            
        except Exception as e:
            logger.error(f"Error scraping Tienda Inglesa: {e}")
        
        logger.info(f"Total Tienda Inglesa products scraped: {len(products)}")
        logger.info(f"Products with EAN: {sum(1 for p in products if p.get('ean'))}")
        return products
    
    def _scrape_product_detail(self, url: str) -> Optional[Dict]:
        """Scrape detailed product page including EAN"""
        try:
            # Add slight pre-request delay
            time.sleep(random.uniform(1, 3))
            
            # Add referer header for authenticity
            request_headers = self.session.headers.copy()
            request_headers['Referer'] = self.category_url
            
            response = self.session.get(url, timeout=30, headers=request_headers)
            
            # Check if blocked - more comprehensive check
            if response.status_code == 403 or response.status_code == 429:
                logger.warning(f"⚠️ HTTP {response.status_code} - Being blocked")
                return None
            
            if 'blocked' in response.text.lower() or 'captcha' in response.text.lower() or 'sorry' in response.text.lower()[:500]:
                logger.warning(f"⚠️ Might be blocked (detected blocking keywords)")
                return None
            
            if response.status_code != 200:
                logger.warning(f"⚠️ Status code {response.status_code}")
                return None
            
            # Check for too short response (likely a block page)
            if len(response.text) < 1000:
                logger.warning(f"⚠️ Response too short ({len(response.text)} chars) - likely blocked")
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            html = response.text
            
            # Extract product name
            name_elem = soup.find('h1') or soup.find(['h2', 'h3'], class_=re.compile(r'product|name|title', re.I))
            if not name_elem:
                logger.debug("No product name found")
                return None
            
            name = name_elem.get_text(strip=True)
            
            # Must be arroz
            if 'arroz' not in name.lower():
                return None
            
            # Exclude non-rice
            exclude_terms = ['chocolate', 'leche', 'yogur', 'pollo', 'carne', 'galleta', 'cereal']
            for term in exclude_terms:
                if term in name.lower() and 'arroz' not in name.lower():
                    return None
            
            # Extract price
            price = None
            price_elem = soup.find(['span', 'div', 'p'], class_=re.compile(r'price|precio|valor', re.I))
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price_match = re.search(r'[\d\.]+', price_text.replace(',', ''))
                if price_match:
                    try:
                        price = float(price_match.group())
                    except:
                        pass
            
            # Extract EAN - search for 13-digit patterns in HTML
            ean = None
            ean_patterns = [
                r'(?:ean|codigo|barcode)["\s:=]+["\']?(\d{13})',  # With label
                r'\b(773\d{10})\b',  # Uruguayan EAN pattern
                r'<[^>]*>(\d{13})</[^>]*>',  # In HTML tags
            ]
            
            for pattern in ean_patterns:
                matches = re.findall(pattern, html, re.I)
                for match in matches:
                    if len(match) == 13 and match.startswith('77'):  # Validate
                        ean = match
                        logger.info(f"✓ Found EAN: {ean}")
                        break
                if ean:
                    break
            
            # Extract brand from name
            brand = None
            brand_patterns = [
                r'\b(TIENDA\s*INGLESA|Saman|Blue\s*Patna|Arrozur|Carolina|Uncle\s*Bens?|Green\s*Chef|Aruba|Monte\s*Cudine|SAMAN|TA-TA)\b'
            ]
            for pattern in brand_patterns:
                match = re.search(pattern, name, re.I)
                if match:
                    brand = match.group(1)
                    break
            
            # Extract image
            image_url = None
            img_elem = soup.find('img', src=True, alt=re.compile(r'producto|product|arroz', re.I))
            if img_elem:
                img_src = img_elem.get('src')
                image_url = img_src if img_src.startswith('http') else self.base_url + img_src
            
            return {
                'supermarket': self.supermarket,
                'name': name,
                'price': price,
                'brand': brand,
                'ean': ean,
                'barcode': ean,
                'category': 'arroz',
                'url': url,
                'image_url': image_url
            }
            
        except Exception as e:
            logger.debug(f"Error scraping product detail: {e}")
            return None
    
    def _parse_product_item(self, item) -> Optional[Dict]:
        """Parse individual product from HTML element"""
        try:
            # Find product name
            name_elem = item.find(['h2', 'h3', 'h4', 'a', 'span'], class_=re.compile(r'name|title|descripcion', re.I))
            if not name_elem:
                return None
            
            name = name_elem.get_text(strip=True)
            if not name or len(name) < 3:
                return None
            
            # FILTER: Must contain "arroz"
            if 'arroz' not in name.lower():
                return None
            
            # Exclude non-rice products (but keep "arroz integral")
            exclude_terms = ['chocolate', 'leche', 'yogur', 'pollo', 'carne', 'galleta']
            for term in exclude_terms:
                if term in name.lower():
                    return None
            
            # Find price
            price = None
            price_elem = item.find(['span', 'div', 'p'], class_=re.compile(r'price|precio|valor', re.I))
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price_match = re.search(r'[\d\.]+', price_text.replace(',', ''))
                if price_match:
                    price = float(price_match.group())
            
            # Find link
            link_elem = item.find('a', href=True)
            url = None
            if link_elem:
                href = link_elem.get('href')
                url = href if href.startswith('http') else self.base_url + href
            
            # Find image
            image_url = None
            img_elem = item.find('img', src=True)
            if img_elem:
                image_url = img_elem.get('src')
            
            # Extract barcode/EAN from various places
            barcode = None
            ean = None
            
            # Look in HTML for EAN/barcode patterns
            item_html = str(item)
            ean_patterns = [
                r'(?:ean|barcode|codigo|gtin)["\s:=]+(\d{8,14})',
                r'(\d{13})',  # Standard EAN-13
                r'data-ean["\s=:]+["\']?(\d{8,14})',
            ]
            
            for pattern in ean_patterns:
                match = re.search(pattern, item_html, re.I)
                if match:
                    candidate = match.group(1)
                    if len(candidate) >= 10:  # Valid barcode length
                        ean = candidate
                        barcode = candidate
                        break
            
            # Extract brand from name
            brand = None
            brand_patterns = [
                r'^(\w+)\s', r'\b(Saman|Arrozur|Blue Patna|Carolina|Uncle Bens?)\b'
            ]
            for pattern in brand_patterns:
                match = re.search(pattern, name, re.I)
                if match:
                    brand = match.group(1)
                    break
            
            product = {
                'supermarket': self.supermarket,
                'name': name,
                'price': price,
                'brand': brand,
                'barcode': barcode,
                'ean': ean,
                'category': 'arroz',
                'url': url,
                'image_url': image_url
            }
            
            return product
            
        except Exception as e:
            logger.debug(f"Error parsing product item: {e}")
            return None
