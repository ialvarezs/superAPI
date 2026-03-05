"""
Complete VTEX scraper for Disco, Devoto, Tata, and Geant
Uses VTEX Intelligent Search API
"""
import requests
import json
import re
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import time
from logger import setup_logger

logger = setup_logger('vtex_complete_scraper')

class VTEXCompleteScraper:
    """Complete scraper for VTEX-based supermarkets using their API"""
    
    def __init__(self, supermarket: str, base_url: str, category_url: str, headers: Dict):
        self.supermarket = supermarket
        self.base_url = base_url
        self.category_url = category_url
        self.headers = headers
        self.session = requests.Session()
        self.session.headers.update(headers)
    
    def scrape_category(self, max_products: int = 500) -> List[Dict]:
        """Scrape arroz category using multiple methods"""
        logger.info(f"Starting {self.supermarket} scrape: {self.category_url}")
        
        products = []
        
        # Method 1: Try VTEX Intelligent Search API
        api_products = self._scrape_via_api()
        if api_products:
            logger.info(f"API method found {len(api_products)} products")
            products.extend(api_products)
        
        # Method 2: Scrape category page and then product detail pages
        if len(products) < 10:
            logger.info("API method insufficient, trying page scraping")
            page_products = self._scrape_via_pages(max_products)
            products.extend(page_products)
        
        # Remove duplicates by SKU
        unique_products = {}
        for p in products:
            sku = p.get('sku')
            if sku and sku not in unique_products:
                unique_products[sku] = p
        
        products = list(unique_products.values())
        logger.info(f"Total unique {self.supermarket} products: {len(products)}")
        return products
    
    def _scrape_via_api(self) -> List[Dict]:
        """Try to use VTEX Intelligent Search API"""
        products = []
        
        # VTEX Intelligent Search API pattern
        # Extract category path from URL
        category_match = re.search(r'/(almacen/[^?]+)', self.category_url)
        if not category_match:
            return products
        
        category_path = category_match.group(1)
        
        # Try VTEX search API
        api_urls = [
            f"{self.base_url}/api/io/_v/api/intelligent-search/product_search/{category_path}?page=0",
            f"{self.base_url}/_v/segment/graphql/v1",
        ]
        
        for api_url in api_urls:
            try:
                logger.info(f"Trying API: {api_url}")
                
                if 'graphql' in api_url:
                    # GraphQL query for products
                    query = {
                        "query": """query ProductSearch($category: String!) {
                            productSearch(category: $category) {
                                products {
                                    productId
                                    productName
                                    brand
                                    items {
                                        itemId
                                        name
                                        ean
                                        sellers {
                                            commertialOffer {
                                                Price
                                                ListPrice
                                                AvailableQuantity
                                            }
                                        }
                                        images { imageUrl }
                                    }
                                }
                            }
                        }""",
                        "variables": {"category": category_path}
                    }
                    response = self.session.post(api_url, json=query, timeout=30)
                else:
                    response = self.session.get(api_url, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    api_products = self._parse_api_response(data)
                    if api_products:
                        products.extend(api_products)
                        logger.info(f"API returned {len(api_products)} products")
                        break
                        
            except Exception as e:
                logger.debug(f"API attempt failed: {e}")
                continue
        
        return products
    
    def _parse_api_response(self, data: Dict) -> List[Dict]:
        """Parse products from API response"""
        products = []
        
        # Try different API response structures
        if 'products' in data:
            for item in data['products']:
                product = self._parse_api_product(item)
                if product:
                    products.append(product)
        
        return products
    
    def _parse_api_product(self, item: Dict) -> Optional[Dict]:
        """Parse single product from API"""
        try:
            # Get first SKU/item
            items = item.get('items', [{}])
            if not items:
                return None
            
            sku_data = items[0]
            
            # Get price from seller
            sellers = sku_data.get('sellers', [{}])
            if sellers:
                offer = sellers[0].get('commertialOffer', {})
                price = offer.get('Price')
                list_price = offer.get('ListPrice')
                in_stock = offer.get('AvailableQuantity', 0) > 0
            else:
                price = None
                list_price = None
                in_stock = False
            
            # Get image
            images = sku_data.get('images', [])
            image_url = images[0].get('imageUrl') if images else None
            
            return {
                'supermarket': self.supermarket,
                'name': item.get('productName'),
                'price': price,
                'original_price': list_price,
                'brand': item.get('brand'),
                'sku': sku_data.get('itemId') or item.get('productId'),
                'ean': sku_data.get('ean'),
                'category': 'arroz',
                'image_url': image_url,
                'url': f"{self.base_url}/{item.get('linkText', '')}/p",
                'in_stock': in_stock
            }
            
        except Exception as e:
            logger.debug(f"Error parsing API product: {e}")
            return None
    
    def _scrape_via_pages(self, max_products: int) -> List[Dict]:
        """Scrape by visiting category pages and product detail pages"""
        products = []
        
        # First try base URL without pagination
        try:
            logger.info(f"Fetching category page (no pagination)")
            response = self.session.get(self.category_url, timeout=30)
                
            response.raise_for_status()
            
            # Extract product links
            soup = BeautifulSoup(response.text, 'html.parser')
            product_links = self._extract_product_links(soup)
            
            logger.info(f"Found {len(product_links)} product links")
            
            # Visit each product page (limit to avoid too many requests)
            for i, link in enumerate(product_links[:50], 1):
                if len(products) >= max_products:
                    break
                
                product = self._scrape_product_page(link)
                if product:
                    products.append(product)
                    logger.info(f"Product {i}/{min(len(product_links), 50)}: {product.get('name', 'Unknown')}")
                
                time.sleep(1.5)  # Rate limit
                
        except Exception as e:
            logger.error(f"Error scraping pages: {e}")
        
        return products
    
    def _extract_product_links(self, soup: BeautifulSoup) -> List[str]:
        """Extract product URLs from category page"""
        links = []
        
        # Look for product links
        for a_tag in soup.find_all('a', href=re.compile(r'/p$|/p\?')):
            href = a_tag.get('href')
            if href:
                full_url = href if href.startswith('http') else self.base_url + href
                if full_url not in links:
                    links.append(full_url)
        
        return links
    
    def _scrape_product_page(self, url: str) -> Optional[Dict]:
        """Scrape individual product detail page"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Extract pageData JSON
            match = re.search(r'window\.pageData\s*=\s*({.*?});', response.text, re.DOTALL)
            if match:
                data = json.loads(match.group(1))
                product_data = data.get('result', {}).get('serverData', {}).get('product', {})
                
                if product_data:
                    return self._parse_product_detail(product_data, url)
            
        except Exception as e:
            logger.debug(f"Error scraping product page {url}: {e}")
        
        return None
    
    def _parse_product_detail(self, data: Dict, url: str) -> Optional[Dict]:
        """Parse product from pageData"""
        try:
            offers = data.get('offers', {})
            offers_list = offers.get('offers', [{}])
            
            price = offers.get('lowPrice')
            if not price and offers_list:
                price = offers_list[0].get('price')
            
            list_price = offers_list[0].get('listPrice') if offers_list else None
            
            # Get images
            images = data.get('image', [])
            image_url = images[0].get('url') if images else None
            
            # Check stock
            in_stock = False
            if offers_list:
                availability = offers_list[0].get('availability', '')
                in_stock = 'InStock' in availability
            
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
                'image_url': image_url,
                'url': url,
                'description': data.get('description'),
                'unit': data.get('measurementUnit'),
                'in_stock': in_stock
            }
            
        except Exception as e:
            logger.error(f"Error parsing product detail: {e}")
            return None
