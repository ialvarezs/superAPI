"""
Specialized scraper for Disco/Devoto/Geant using search with better extraction
"""
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import json
import re
import time
from typing import List, Dict, Optional
from logger import setup_logger

logger = setup_logger('search_scraper')

class SearchBasedScraper:
    """Scraper using search functionality and extracting from product cards"""
    
    def __init__(self, supermarket: str, base_url: str, search_term: str = "arroz"):
        self.supermarket = supermarket
        self.base_url = base_url
        self.search_url = f"{base_url}/?q={search_term}"
        self.search_term = search_term
    
    def scrape_category(self, max_products: int = 100) -> List[Dict]:
        """Scrape products using search"""
        logger.info(f"Starting search-based scrape for {self.supermarket}: {self.search_url}")
        
        products = []
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )
            page = context.new_page()
            
            try:
                page.goto(self.search_url, wait_until='domcontentloaded', timeout=60000)
                logger.info(f"Page loaded, waiting for content...")
                time.sleep(5)
                
                # Scroll extensively to load lazy products
                for i in range(15):
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(1)
                
                # Extract products from page
                products_data = page.evaluate("""
                    () => {
                        const products = [];
                        
                        // Try multiple selectors
                        const selectors = [
                            '[data-testid*="product-card"]',
                            '[class*="productCard"]',
                            '[class*="product-card"]',
                            '[class*="ProductCard"]',
                            'article',
                            '[data-product-id]'
                        ];
                        
                        let elements = [];
                        for (const selector of selectors) {
                            elements = document.querySelectorAll(selector);
                            if (elements.length > 0) break;
                        }
                        
                        elements.forEach(el => {
                            try {
                                // Extract product data
                                const nameEl = el.querySelector('h2, h3, [class*="name"], [class*="Name"], [class*="title"]');
                                const priceEl = el.querySelector('[class*="price"], [class*="Price"], [data-price]');
                                const linkEl = el.querySelector('a[href]');
                                const imgEl = el.querySelector('img');
                                const brandEl = el.querySelector('[class*="brand"], [class*="Brand"]');
                                
                                const name = nameEl?.textContent?.trim();
                                const price = priceEl?.textContent?.trim();
                                const link = linkEl?.href;
                                const img = imgEl?.src;
                                const brand = brandEl?.textContent?.trim();
                                
                                if (name && link) {
                                    products.push({
                                        name: name,
                                        price: price,
                                        url: link,
                                        image_url: img,
                                        brand: brand
                                    });
                                }
                            } catch (e) {
                                // Skip errors
                            }
                        });
                        
                        return products;
                    }
                """)
                
                logger.info(f"Extracted {len(products_data)} products from DOM")
                
                # Parse and filter products
                for p_data in products_data:
                    product = self._parse_product(p_data)
                    if product and self._is_arroz_product(product):
                        products.append(product)
                        if len(products) >= max_products:
                            break
                
            except Exception as e:
                logger.error(f"Error scraping {self.supermarket}: {e}")
            finally:
                browser.close()
        
        logger.info(f"Scraped {len(products)} arroz products from {self.supermarket}")
        return products
    
    def _parse_product(self, data: Dict) -> Optional[Dict]:
        """Parse product data"""
        try:
            name = data.get('name', '').strip()
            if not name or len(name) < 3:
                return None
            
            # Parse price
            price = None
            price_text = data.get('price', '')
            if price_text:
                # Extract numeric value
                price_match = re.search(r'[\d,\.]+', str(price_text).replace('.', '').replace(',', '.'))
                if price_match:
                    try:
                        price = float(price_match.group())
                    except:
                        pass
            
            return {
                'supermarket': self.supermarket,
                'name': name,
                'price': price,
                'brand': data.get('brand'),
                'url': data.get('url'),
                'image_url': data.get('image_url'),
                'category': 'arroz'
            }
            
        except Exception as e:
            logger.debug(f"Error parsing product: {e}")
            return None
    
    def _is_arroz_product(self, product: Dict) -> bool:
        """Filter to ensure it's actually rice"""
        name = (product.get('name') or '').lower()
        
        # Must contain arroz
        if 'arroz' not in name:
            return False
        
        # Exclude non-rice
        exclude = ['chocolate', 'leche', 'yogur', 'pollo', 'carne', 'notebook', 
                  'celular', 'cable', 'electro', 'mueble', 'ropa', 'juguete',
                  'limpieza', 'shampoo', 'crema', 'pan', 'fideos', 'galleta']
        
        for term in exclude:
            if term in name:
                return False
        
        return True
