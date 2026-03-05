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
        product_urls = []
        
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
                
                # Extract product URLs
                product_urls = page.evaluate("""
                    () => {
                        const urls = new Set();
                        document.querySelectorAll('a[href*="/product/"]').forEach(a => {
                            const href = a.href;
                            const text = a.textContent.toLowerCase();
                            if (text.includes('arroz') || href.toLowerCase().includes('arroz')) {
                                urls.add(href);
                            }
                        });
                        return Array.from(urls);
                    }
                """)
                
                logger.info(f"Found {len(product_urls)} product URLs")
                
                # Visit each product page to get detailed data including EAN
                for i, url in enumerate(product_urls[:max_products], 1):
                    try:
                        logger.info(f"Scraping product {i}/{min(len(product_urls), max_products)}")
                        product = self._scrape_product_detail(page, url)
                        if product:
                            products.append(product)
                        time.sleep(1.5)
                    except Exception as e:
                        logger.error(f"Error scraping {url}: {e}")
                        continue
                
            except Exception as e:
                logger.error(f"Error scraping {self.supermarket}: {e}")
            finally:
                browser.close()
        
        logger.info(f"Scraped {len(products)} arroz products from {self.supermarket}")
        return products
    
    def _scrape_product_detail(self, page, url: str) -> Optional[Dict]:
        """Scrape detailed product page including EAN from meta"""
        try:
            page.goto(url, wait_until='domcontentloaded', timeout=30000)
            time.sleep(2)
            
            # Extract comprehensive data
            product_data = page.evaluate("""
                () => {
                    // Get meta keywords (contains EAN!)
                    const metaKeywords = document.querySelector('meta[name="keywords"]')?.content || '';
                    const keywordParts = metaKeywords.split(',').map(k => k.trim());
                    
                    // Find EAN (13-digit number in keywords)
                    const eanFromMeta = keywordParts.find(k => /^\d{13}$/.test(k));
                    
                    // Get product info
                    const name = document.querySelector('h1, [class*="productName"]')?.textContent?.trim();
                    const priceEl = document.querySelector('[class*="price"], [data-testid*="price"]');
                    const priceText = priceEl?.textContent?.trim();
                    const brand = document.querySelector('[class*="brand"]')?.textContent?.trim();
                    const img = document.querySelector('img[src*="vtex"]')?.src;
                    
                    // Get SKU from URL
                    const sku = window.location.pathname.match(/\/(\d+)$/)?.[1];
                    
                    return {
                        name, priceText, brand, img, eanFromMeta, sku, metaKeywords
                    };
                }
            """)
            
            if not product_data.get('name'):
                return None
            
            name = product_data['name']
            
            # Must be arroz
            if not self._is_arroz_product({'name': name}):
                return None
            
            # Parse price
            price = None
            price_text = product_data.get('priceText', '')
            if price_text:
                price_match = re.search(r'[\d,\.]+', price_text.replace('.', '').replace(',', '.'))
                if price_match:
                    try:
                        price = float(price_match.group())
                    except:
                        pass
            
            # Extract brand from name if not found
            brand = product_data.get('brand')
            if not brand:
                brand_patterns = [
                    r'\b(Saman|Blue\s*Patna|Arrozur|Carolina|Uncle\s*Bens?|Green\s*Chef|Aruba|Ta-Ta|Monte\s*Cudine)\b'
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
                'ean': product_data.get('eanFromMeta'),
                'barcode': product_data.get('eanFromMeta'),
                'sku': product_data.get('sku'),
                'category': 'arroz',
                'url': url,
                'image_url': product_data.get('img')
            }
            
            if product.get('ean'):
                logger.info(f"✓ Found EAN: {product['ean']} for {name[:40]}")
            
            return product
                
        except Exception as e:
            logger.debug(f"Error scraping product detail: {e}")
        
        return None
    
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
