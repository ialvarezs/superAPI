"""
Enhanced Tienda Inglesa scraper for arroz category
"""
import requests
from bs4 import BeautifulSoup
import re
import time
from typing import List, Dict, Optional
from logger import setup_logger

logger = setup_logger('tienda_inglesa_scraper')

class TiendaInglesaScraper:
    """Scraper for Tienda Inglesa supermarket"""
    
    def __init__(self, base_url: str, category_url: str, headers: Dict):
        self.supermarket = "tienda_inglesa"
        self.base_url = base_url
        self.category_url = category_url
        self.headers = headers
        self.session = requests.Session()
        self.session.headers.update(headers)
    
    def scrape_category(self, max_pages: int = 20) -> List[Dict]:
        """Scrape arroz category from Tienda Inglesa"""
        logger.info(f"Starting Tienda Inglesa scrape: {self.category_url}")
        
        products = []
        
        try:
            response = self.session.get(self.category_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find product cards
            product_items = soup.find_all(['div', 'article'], class_=re.compile(r'product|item', re.I))
            
            logger.info(f"Found {len(product_items)} potential product items")
            
            for item in product_items:
                product = self._parse_product_item(item)
                if product:
                    products.append(product)
                    logger.debug(f"Parsed product: {product.get('name')}")
            
            # Try pagination if exists
            next_page = soup.find('a', class_=re.compile(r'next|siguiente', re.I))
            page_num = 2
            
            while next_page and page_num <= max_pages:
                time.sleep(2)
                try:
                    next_url = next_page.get('href')
                    if not next_url.startswith('http'):
                        next_url = self.base_url + next_url
                    
                    logger.info(f"Fetching page {page_num}")
                    response = self.session.get(next_url, timeout=30)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    page_products = soup.find_all(['div', 'article'], class_=re.compile(r'product|item', re.I))
                    for item in page_products:
                        product = self._parse_product_item(item)
                        if product:
                            products.append(product)
                    
                    next_page = soup.find('a', class_=re.compile(r'next|siguiente', re.I))
                    page_num += 1
                    
                except Exception as e:
                    logger.error(f"Error on page {page_num}: {e}")
                    break
            
        except Exception as e:
            logger.error(f"Error scraping Tienda Inglesa: {e}")
        
        logger.info(f"Total Tienda Inglesa products scraped: {len(products)}")
        return products
    
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
            ean_match = re.search(r'(?:ean|barcode|codigo)["\s:=]+(\d{8,14})', str(item), re.I)
            if ean_match:
                barcode = ean_match.group(1)
            
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
                'category': 'arroz',
                'url': url,
                'image_url': image_url
            }
            
            return product
            
        except Exception as e:
            logger.debug(f"Error parsing product item: {e}")
            return None
