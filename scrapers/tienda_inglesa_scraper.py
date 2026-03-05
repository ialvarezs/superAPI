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
        product_urls = []
        
        try:
            response = self.session.get(self.category_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # First pass: collect product URLs
            for item in soup.find_all(['div', 'article'], class_=re.compile(r'product|item', re.I)):
                link_elem = item.find('a', href=True)
                if link_elem:
                    href = link_elem.get('href')
                    url = href if href.startswith('http') else self.base_url + href
                    
                    # Quick filter by name in link
                    text = link_elem.get_text().lower()
                    if 'arroz' in text or 'arroz' in href.lower():
                        if url not in product_urls:
                            product_urls.append(url)
            
            logger.info(f"Found {len(product_urls)} potential arroz product URLs")
            
            # Second pass: visit each product page for detailed data
            for i, url in enumerate(product_urls[:100], 1):
                try:
                    logger.info(f"Fetching product {i}/{min(len(product_urls), 100)}")
                    product = self._scrape_product_detail(url)
                    if product:
                        products.append(product)
                    time.sleep(1.5)  # Rate limiting
                except Exception as e:
                    logger.error(f"Error fetching product {url}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error scraping Tienda Inglesa: {e}")
        
        logger.info(f"Total Tienda Inglesa products scraped: {len(products)}")
        return products
    
    def _scrape_product_detail(self, url: str) -> Optional[Dict]:
        """Scrape detailed product page"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            html = response.text
            
            # Extract product name
            name_elem = soup.find('h1') or soup.find(['h2', 'h3'], class_=re.compile(r'product|name|title', re.I))
            if not name_elem:
                return None
            
            name = name_elem.get_text(strip=True)
            
            # Must be arroz
            if 'arroz' not in name.lower():
                return None
            
            # Exclude non-rice
            exclude_terms = ['chocolate', 'leche', 'yogur', 'pollo', 'carne', 'galleta']
            for term in exclude_terms:
                if term in name.lower():
                    return None
            
            # Extract price
            price = None
            price_elem = soup.find(['span', 'div', 'p'], class_=re.compile(r'price|precio|valor', re.I))
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price_match = re.search(r'[\d\.]+', price_text.replace(',', ''))
                if price_match:
                    price = float(price_match.group())
            
            # Extract EAN - search in HTML source
            ean = None
            ean_patterns = [
                r'(?:ean|codigo)["\s:=]+["\']?(\d{13})',
                r'(\d{13})',  # 13-digit number
                r'7730\d{9}',  # Uruguayan EAN pattern
            ]
            
            for pattern in ean_patterns:
                match = re.search(pattern, html, re.I)
                if match:
                    candidate = match.group(1) if '(' in pattern else match.group(0)
                    if len(candidate) == 13:
                        ean = candidate
                        break
            
            # Extract brand from name
            brand = None
            brand_patterns = [
                r'\b(Saman|Blue\s*Patna|Arrozur|Carolina|Uncle\s*Bens?|Green\s*Chef|Aruba|Monte\s*Cudine)\b'
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
                image_url = img_elem.get('src')
            
            return {
                'supermarket': self.supermarket,
                'name': name,
                'price': price,
                'brand': brand,
                'ean': ean,
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
