"""
Generic VTEX scraper for Disco, Devoto, Tata, and Geant
"""
import requests
import json
import re
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import time
from logger import setup_logger

logger = setup_logger('vtex_scraper')

class VTEXScraper:
    """Generic scraper for VTEX-based supermarkets"""
    
    def __init__(self, supermarket: str, base_url: str, category_url: str, headers: Dict):
        self.supermarket = supermarket
        self.base_url = base_url
        self.category_url = category_url
        self.headers = headers
        self.session = requests.Session()
        self.session.headers.update(headers)
    
    def scrape_category(self, max_pages: int = 10) -> List[Dict]:
        """Scrape all products from arroz category"""
        logger.info(f"Starting scrape for {self.supermarket} - {self.category_url}")
        
        products = []
        page = 1
        
        while page <= max_pages:
            try:
                url = f"{self.category_url}?page={page}"
                logger.info(f"Fetching page {page}: {url}")
                
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                # Extract pageData JSON from page
                page_products = self._extract_products_from_page(response.text)
                
                if not page_products:
                    logger.info(f"No products found on page {page}, stopping")
                    break
                
                products.extend(page_products)
                logger.info(f"Found {len(page_products)} products on page {page}")
                
                page += 1
                time.sleep(2)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error scraping page {page}: {e}")
                break
        
        logger.info(f"Total products scraped: {len(products)}")
        return products
    
    def _extract_products_from_page(self, html: str) -> List[Dict]:
        """Extract product data from VTEX page HTML"""
        products = []
        
        try:
            # Try to find window.__RUNTIME__ or window.pageData
            runtime_match = re.search(r'window\.__RUNTIME__\s*=\s*({.*?});', html, re.DOTALL)
            pagedata_match = re.search(r'window\.pageData\s*=\s*({.*?});/\*\]\]>\*/', html, re.DOTALL)
            
            if pagedata_match:
                data = json.loads(pagedata_match.group(1))
                # This is a product detail page
                product_data = data.get('result', {}).get('serverData', {}).get('product', {})
                if product_data:
                    product = self._parse_product_detail(product_data)
                    if product:
                        products.append(product)
            
            elif runtime_match:
                # Category listing page
                runtime_data = json.loads(runtime_match.group(1))
                # Extract product list from runtime data
                products = self._parse_category_runtime(runtime_data)
            
            # Fallback: parse HTML directly for product cards
            if not products:
                products = self._parse_html_products(html)
                
        except Exception as e:
            logger.error(f"Error extracting products: {e}")
        
        return products
    
    def _parse_product_detail(self, data: Dict) -> Optional[Dict]:
        """Parse single product from pageData"""
        try:
            offers = data.get('offers', {})
            price = offers.get('lowPrice') or offers.get('offers', [{}])[0].get('price')
            list_price = offers.get('offers', [{}])[0].get('listPrice')
            
            return {
                'supermarket': self.supermarket,
                'name': data.get('name'),
                'price': price,
                'original_price': list_price,
                'brand': data.get('brand', {}).get('name') if isinstance(data.get('brand'), dict) else data.get('brand'),
                'sku': data.get('sku'),
                'ean': data.get('ean'),
                'gtin': data.get('gtin'),
                'category': 'arroz',
                'image_url': data.get('image', [{}])[0].get('url') if data.get('image') else None,
                'url': f"{self.base_url}/{data.get('slug')}",
                'description': data.get('description'),
                'unit': data.get('measurementUnit'),
                'in_stock': True
            }
        except Exception as e:
            logger.error(f"Error parsing product detail: {e}")
            return None
    
    def _parse_category_runtime(self, runtime_data: Dict) -> List[Dict]:
        """Parse products from __RUNTIME__ data"""
        products = []
        
        # VTEX stores product data in different locations
        # Need to traverse the runtime object to find products
        
        return products
    
    def _parse_html_products(self, html: str) -> List[Dict]:
        """Fallback: parse product cards from HTML"""
        products = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Look for product cards (varies by VTEX theme)
        product_cards = soup.find_all(['article', 'div'], class_=re.compile(r'product|item|card'))
        
        for card in product_cards[:50]:  # Limit to avoid false positives
            try:
                # Try to extract basic info
                name_elem = card.find(['h2', 'h3', 'a'], class_=re.compile(r'name|title|product'))
                price_elem = card.find(['span', 'div'], class_=re.compile(r'price|valor'))
                link_elem = card.find('a', href=True)
                
                if name_elem and link_elem:
                    product = {
                        'supermarket': self.supermarket,
                        'name': name_elem.get_text(strip=True),
                        'url': self.base_url + link_elem['href'] if link_elem['href'].startswith('/') else link_elem['href'],
                        'category': 'arroz'
                    }
                    
                    if price_elem:
                        price_text = price_elem.get_text(strip=True)
                        price_match = re.search(r'[\d,\.]+', price_text.replace('.', '').replace(',', '.'))
                        if price_match:
                            product['price'] = float(price_match.group())
                    
                    products.append(product)
                    
            except Exception as e:
                continue
        
        return products
    
    def get_product_details(self, product_url: str) -> Optional[Dict]:
        """Fetch detailed product information"""
        try:
            logger.info(f"Fetching product details: {product_url}")
            response = self.session.get(product_url, timeout=30)
            response.raise_for_status()
            
            page_products = self._extract_products_from_page(response.text)
            return page_products[0] if page_products else None
            
        except Exception as e:
            logger.error(f"Error fetching product details: {e}")
            return None
