"""
Enhanced Tienda Inglesa scraper for arroz category with EAN extraction
"""
import requests
from bs4 import BeautifulSoup
import re
import time
import random
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
        # Additional headers to avoid blocking
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-UY,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def scrape_category(self, max_pages: int = 20, max_products: int = 30) -> List[Dict]:
        """Scrape arroz category from Tienda Inglesa - with product detail visits for EAN"""
        logger.info(f"Starting Tienda Inglesa scrape: {self.category_url}")
        
        products = []
        product_urls = []
        
        try:
            response = self.session.get(self.category_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find product cards and extract URLs
            product_items = soup.find_all(['div', 'article'], class_=re.compile(r'product|item', re.I))
            
            logger.info(f"Found {len(product_items)} potential product items")
            
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
                    # Random delay between 8-15 seconds (human-like)
                    if i > 1:
                        delay = random.randint(8, 15)
                        logger.info(f"Waiting {delay}s before next request...")
                        time.sleep(delay)
                    
                    logger.info(f"Fetching product {i}/{min(len(product_urls), max_products)}: {url[:80]}...")
                    product = self._scrape_product_detail(url)
                    
                    if product:
                        products.append(product)
                        if product.get('ean'):
                            logger.info(f"✓ Product with EAN: {product['name'][:50]} - {product['ean']}")
                    
                except Exception as e:
                    logger.error(f"Error fetching product: {e}")
                    # Long pause on error (might be getting blocked)
                    time.sleep(30)
                    continue
            
        except Exception as e:
            logger.error(f"Error scraping Tienda Inglesa: {e}")
        
        logger.info(f"Total Tienda Inglesa products scraped: {len(products)}")
        logger.info(f"Products with EAN: {sum(1 for p in products if p.get('ean'))}")
        return products
    
    def _scrape_product_detail(self, url: str) -> Optional[Dict]:
        """Scrape detailed product page including EAN"""
        try:
            response = self.session.get(url, timeout=30)
            
            # Check if blocked
            if 'blocked' in response.text.lower() or 'sorry' in response.text.lower()[:200]:
                logger.warning(f"⚠️ Might be blocked, skipping URL")
                return None
            
            if response.status_code != 200:
                return None
            
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
