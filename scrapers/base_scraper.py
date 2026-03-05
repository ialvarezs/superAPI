"""
Base scraper class for supermarket websites
"""
import time
import requests
import re
import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from typing import List, Dict, Optional
import pandas as pd


class BaseScraper:
    def __init__(self, supermarket_config: Dict):
        self.config = supermarket_config
        self.name = supermarket_config['name']
        self.base_url = supermarket_config['base_url']
        self.headers = supermarket_config.get('headers', {})

        # Setup Chrome options for headless browsing
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--window-size=1920,1080')
        self.chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        self.chrome_options.add_argument('--disable-extensions')
        self.chrome_options.add_argument(f"--user-agent={self.headers.get('User-Agent', '')}")

        # Set Chrome binary path for macOS
        self.chrome_options.binary_location = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'

        self.driver = None

    def start_browser(self):
        """Initialize the browser"""
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=self.chrome_options)
        return self.driver

    def close_browser(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()

    def find_lacteos_url(self) -> Optional[str]:
        """Find the lacteos category URL by exploring the website"""
        if not self.driver:
            self.start_browser()

        try:
            self.driver.get(self.base_url)
            time.sleep(3)

            # Common patterns for dairy/lacteos links
            patterns = [
                "//a[contains(text(), 'Lácteos')]",
                "//a[contains(text(), 'lacteos')]",
                "//a[contains(text(), 'Lácteo')]",
                "//a[contains(text(), 'Dairy')]",
                "//a[contains(text(), 'Leche')]",
                "//a[contains(@href, 'lacteos')]",
                "//a[contains(@href, 'dairy')]",
                "//a[contains(@href, 'leche')]"
            ]

            for pattern in patterns:
                try:
                    element = self.driver.find_element(By.XPATH, pattern)
                    href = element.get_attribute('href')
                    if href:
                        print(f"Found lacteos URL for {self.name}: {href}")
                        return href
                except:
                    continue

            # Try to find category navigation
            try:
                # Look for common category menu structures
                category_elements = self.driver.find_elements(By.CSS_SELECTOR,
                    "nav a, .category a, .menu a, .nav-item a")

                for element in category_elements:
                    text = element.text.lower()
                    href = element.get_attribute('href')
                    if any(word in text for word in ['lácteo', 'lacteo', 'leche', 'dairy']) and href:
                        print(f"Found potential lacteos URL for {self.name}: {href}")
                        return href
            except:
                pass

            print(f"Could not find lacteos URL for {self.name}")
            return None

        except Exception as e:
            print(f"Error finding lacteos URL for {self.name}: {e}")
            return None

    def extract_barcode(self, text: str) -> Optional[str]:
        """Extract barcode from product text"""
        if not text:
            return None

        # Common barcode patterns
        patterns = [
            r'EAN[:\s]*(\d{8,14})',
            r'UPC[:\s]*(\d{8,14})',
            r'Código[:\s]*(\d{8,14})',
            r'COD[:\s]*(\d{8,14})',
            r'\b(\d{13})\b',  # 13-digit EAN
            r'\b(\d{12})\b',  # 12-digit UPC
            r'\b(\d{8})\b'    # 8-digit codes
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def clean_price(self, price_text: str) -> Optional[float]:
        """Clean and convert price text to float"""
        if not price_text:
            return None

        # Remove currency symbols and extra text
        price_text = re.sub(r'[^\d,.]', '', price_text)
        price_text = price_text.replace(',', '.')

        try:
            return float(price_text)
        except:
            return None

    def normalize_product_name(self, name: str) -> str:
        """Normalize product name for comparison"""
        if not name:
            return ""

        name = name.lower().strip()
        # Remove brand suffixes, sizes, etc.
        name = re.sub(r'\s+\d+\s*(ml|l|g|kg|gr|cc)\b', '', name)
        name = re.sub(r'\s+x\s*\d+', '', name)
        name = re.sub(r'\s{2,}', ' ', name)
        return name.strip()

    def scrape_lacteos_products(self, lacteos_url: str) -> List[Dict]:
        """Scrape dairy products from the given URL"""
        if not self.driver:
            self.start_browser()

        products = []

        try:
            self.driver.get(lacteos_url)
            time.sleep(5)

            # Try to load more products if pagination exists
            self.handle_pagination()

            # Extract products using different selectors
            products = self.extract_products()

        except Exception as e:
            print(f"Error scraping {self.name}: {e}")

        return products

    def handle_pagination(self):
        """Handle pagination to load more products"""
        try:
            # Look for "Load More", "Ver más", "Cargar más" buttons
            load_more_selectors = [
                "button[contains(text(), 'Ver más')]",
                "button[contains(text(), 'Cargar más')]",
                "button[contains(text(), 'Load more')]",
                ".load-more",
                ".btn-load-more"
            ]

            for selector in load_more_selectors:
                try:
                    button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if button.is_displayed():
                        self.driver.execute_script("arguments[0].click();", button)
                        time.sleep(3)
                        break
                except:
                    continue

        except Exception as e:
            print(f"Could not handle pagination for {self.name}: {e}")

    def extract_products(self) -> List[Dict]:
        """Extract products from the current page"""
        products = []

        # Common product container selectors
        product_selectors = [
            ".product-item",
            ".product",
            ".item",
            ".card",
            ".product-card",
            ".grid-item",
            "[data-product]"
        ]

        product_elements = []
        for selector in product_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    product_elements = elements
                    break
            except:
                continue

        if not product_elements:
            # Fallback: try to find any container with product-like information
            product_elements = self.driver.find_elements(By.CSS_SELECTOR, "*[class*='product'], *[id*='product']")

        print(f"Found {len(product_elements)} potential products for {self.name}")

        for element in product_elements[:50]:  # Limit to first 50 products
            try:
                product = self.extract_product_info(element)
                if product and product.get('name'):
                    products.append(product)
            except Exception as e:
                print(f"Error extracting product: {e}")
                continue

        return products

    def extract_product_info(self, element) -> Dict:
        """Extract individual product information"""
        product = {
            'supermarket': self.name,
            'name': None,
            'price': None,
            'original_price': None,
            'brand': None,
            'barcode': None,
            'image_url': None,
            'url': None,
            'description': None
        }

        try:
            # Extract product name
            name_selectors = [
                ".product-title", ".title", ".name", ".product-name",
                "h1", "h2", "h3", "h4", ".heading", "[class*='title']"
            ]

            for selector in name_selectors:
                try:
                    name_elem = element.find_element(By.CSS_SELECTOR, selector)
                    if name_elem.text.strip():
                        product['name'] = name_elem.text.strip()
                        break
                except:
                    continue

            # Extract price
            price_selectors = [
                ".price", ".precio", ".cost", "[class*='price']",
                "[data-price]", ".amount"
            ]

            for selector in price_selectors:
                try:
                    price_elem = element.find_element(By.CSS_SELECTOR, selector)
                    if price_elem.text.strip():
                        product['price'] = self.clean_price(price_elem.text.strip())
                        product['original_price'] = price_elem.text.strip()
                        break
                except:
                    continue

            # Extract image URL
            try:
                img = element.find_element(By.CSS_SELECTOR, "img")
                product['image_url'] = img.get_attribute('src') or img.get_attribute('data-src')
            except:
                pass

            # Extract product URL
            try:
                link = element.find_element(By.CSS_SELECTOR, "a")
                href = link.get_attribute('href')
                if href:
                    product['url'] = href if href.startswith('http') else self.base_url + href
            except:
                pass

            # Try to extract barcode from text content
            full_text = element.text
            product['barcode'] = self.extract_barcode(full_text)

        except Exception as e:
            print(f"Error extracting product info: {e}")

        return product

    def save_products(self, products: List[Dict], filename: str):
        """Save products to JSON and CSV files"""
        if not products:
            print(f"No products to save for {self.name}")
            return

        # Save as JSON
        json_file = f"data/{filename}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(products, f, ensure_ascii=False, indent=2)

        # Save as CSV
        csv_file = f"data/{filename}.csv"
        df = pd.DataFrame(products)
        df.to_csv(csv_file, index=False, encoding='utf-8')

        print(f"Saved {len(products)} products for {self.name} to {json_file} and {csv_file}")

    def run_scraping(self) -> List[Dict]:
        """Main method to run the scraping process"""
        print(f"Starting scraping for {self.name}")

        try:
            self.start_browser()

            # Find lacteos URL
            lacteos_url = self.find_lacteos_url()

            if not lacteos_url:
                print(f"Could not find lacteos URL for {self.name}")
                return []

            # Scrape products
            products = self.scrape_lacteos_products(lacteos_url)

            # Save products
            if products:
                self.save_products(products, f"{self.name.lower().replace(' ', '_')}_lacteos")

            return products

        except Exception as e:
            print(f"Error in scraping {self.name}: {e}")
            return []

        finally:
            self.close_browser()