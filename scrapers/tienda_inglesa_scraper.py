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
        """Scrape arroz category from Tienda Inglesa using Selenium"""
        logger.info(f"Starting Tienda Inglesa scrape: {self.category_url}")
        logger.info(f"Will scrape maximum {max_products} products with 0.5-1 second delays")
        
        products = []
        product_urls = []
        
        try:
            # Create stealth browser
            logger.info("Creating stealth browser...")
            self.driver = self.create_stealth_browser()
            
            # Step 1: Visit Google first (appear human)
            logger.info("Step 1: Visiting Google...")
            self.driver.get('https://www.google.com')
            self.human_like_delay(2, 4)
            
            # Step 2: Visit category page
            logger.info(f"Step 2: Visiting category page...")
            self.driver.get(self.category_url)
            self.human_like_delay(3, 5)
            
            # Wait for products to load
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "a"))
                )
            except:
                logger.warning("Timeout waiting for page load")
            
            # Get page source
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            logger.info(f"Page loaded, length: {len(html)}")
            
            # Find all product links
            all_links = soup.find_all('a', href=re.compile(r'producto', re.I))
            logger.info(f"Found {len(all_links)} product links")
            
            for link in all_links:
                href = link.get('href')
                url = href if href.startswith('http') else self.base_url + href
                link_text = link.get_text().lower()
                
                # Filter by arroz
                if 'arroz' in link_text or 'arroz' in url.lower():
                    if url not in product_urls:
                        product_urls.append(url)
            
            logger.info(f"Found {len(product_urls)} arroz product URLs")
            
            # Visit product detail pages with human-like delays
            for i, url in enumerate(product_urls[:max_products], 1):
                try:
                    # Human-like delay between 0.5-1 seconds
                    if i > 1:
                        delay = random.uniform(0.5, 1.0)
                        logger.info(f"Waiting {delay:.1f}s before next request...")
                        time.sleep(delay)
                    
                    logger.info(f"Fetching product {i}/{min(len(product_urls), max_products)}: {url[:80]}...")
                    product = self._scrape_product_detail(url)
                    
                    if product:
                        products.append(product)
                        if product.get('ean'):
                            logger.info(f"✓ Product with EAN: {product['name'][:50]} - {product['ean']}")
                    else:
                        logger.warning("Product returned None")
                    
                except Exception as e:
                    logger.error(f"Error fetching product: {e}")
                    time.sleep(3)
                    continue
            
        except Exception as e:
            logger.error(f"Error scraping Tienda Inglesa: {e}")
        finally:
            # Close browser
            if self.driver:
                logger.info("Closing browser...")
                self.driver.quit()
        
        logger.info(f"Total Tienda Inglesa products scraped: {len(products)}")
        logger.info(f"Products with EAN: {sum(1 for p in products if p.get('ean'))}")
        return products
    
    def _scrape_product_detail(self, url: str) -> Optional[Dict]:
        """Scrape detailed product page including EAN using Selenium"""
        try:
            # Navigate to product page
            self.driver.get(url)
            self.human_like_delay(0.5, 1.0)
            
            # Wait for product content to load
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "h1"))
                )
            except:
                logger.warning("Timeout waiting for product page")
            
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # Check for too short response (likely a block page)
            if len(html) < 1000:
                logger.warning(f"⚠️ Response too short ({len(html)} chars) - likely blocked")
                return None
            
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
