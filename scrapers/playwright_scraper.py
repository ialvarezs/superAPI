"""
Playwright-based scraper for JavaScript-rendered sites (Tata, Disco, Devoto, Geant)
"""
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import json
import re
import time
from typing import List, Dict, Optional
from logger import setup_logger

logger = setup_logger('playwright_scraper')

class PlaywrightScraper:
    """Scraper using Playwright for JS-rendered sites"""
    
    def __init__(self, supermarket: str, base_url: str, category_url: str):
        self.supermarket = supermarket
        self.base_url = base_url
        self.category_url = category_url
    
    def scrape_category(self, max_products: int = 100) -> List[Dict]:
        """Scrape category using Playwright"""
        logger.info(f"Starting Playwright scrape for {self.supermarket}: {self.category_url}")
        
        products = []
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()
            
            try:
                # Load category page
                logger.info(f"Loading category page...")
                page.goto(self.category_url, wait_until='networkidle', timeout=60000)
                
                # Wait for products to load
                page.wait_for_timeout(3000)
                
                # Scroll multiple times to load all products
                for i in range(10):
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(1500)
                
                # Extract product links from rendered page
                product_links = page.evaluate("""
                    () => {
                        const links = new Set();
                        document.querySelectorAll('a[href]').forEach(a => {
                            const href = a.href;
                            if (href.includes('/p') && (href.includes('arroz') || a.textContent.toLowerCase().includes('arroz'))) {
                                links.add(href);
                            }
                        });
                        return Array.from(links);
                    }
                """)
                
                logger.info(f"Found {len(product_links)} product links")
                
                # Visit each product page
                for i, link in enumerate(product_links[:max_products], 1):
                    try:
                        logger.info(f"Scraping product {i}/{min(len(product_links), max_products)}")
                        product = self._scrape_product_page(page, link)
                        if product:
                            products.append(product)
                        time.sleep(1)
                    except Exception as e:
                        logger.error(f"Error scraping product {link}: {e}")
                        continue
                
            except Exception as e:
                logger.error(f"Error scraping category: {e}")
            finally:
                browser.close()
        
        logger.info(f"Scraped {len(products)} products from {self.supermarket}")
        return products
    
    def _scroll_page(self, page):
        """Scroll page to trigger lazy loading"""
        try:
            for _ in range(3):
                page.evaluate("window.scrollBy(0, window.innerHeight)")
                time.sleep(1)
        except:
            pass
    
    def _scrape_product_page(self, page, url: str) -> Optional[Dict]:
        """Scrape individual product page"""
        try:
            page.goto(url, wait_until='domcontentloaded', timeout=30000)
            time.sleep(2)  # Let JS execute
            
            # Extract pageData from window object
            page_data = page.evaluate("() => window.pageData")
            
            if page_data:
                product_data = page_data.get('result', {}).get('serverData', {}).get('product', {})
                if product_data:
                    return self._parse_product_data(product_data, url)
            
            # Fallback: parse from DOM
            product = page.evaluate("""
                () => {
                    const name = document.querySelector('h1')?.textContent?.trim();
                    const priceEl = document.querySelector('[data-price], .price, [class*="price"]');
                    const price = priceEl?.textContent?.match(/[\\d,\\.]+/)?.[0];
                    const brand = document.querySelector('[data-brand], .brand')?.textContent?.trim();
                    const img = document.querySelector('img[src*="vtexassets"], img[src*="vteximg"]')?.src;
                    
                    return { name, price, brand, img };
                }
            """)
            
            if product.get('name'):
                return {
                    'supermarket': self.supermarket,
                    'name': product['name'],
                    'price': float(product['price'].replace(',', '.')) if product.get('price') else None,
                    'brand': product.get('brand'),
                    'image_url': product.get('img'),
                    'url': url,
                    'category': 'arroz'
                }
                
        except Exception as e:
            logger.debug(f"Error scraping product page: {e}")
        
        return None
    
    def _parse_product_data(self, data: Dict, url: str) -> Optional[Dict]:
        """Parse product from pageData JSON"""
        try:
            offers = data.get('offers', {})
            offers_list = offers.get('offers', [{}])
            
            price = offers.get('lowPrice')
            if not price and offers_list:
                price = offers_list[0].get('price')
            
            list_price = offers_list[0].get('listPrice') if offers_list else None
            
            images = data.get('image', [])
            image_url = images[0].get('url') if images else None
            
            in_stock = False
            if offers_list:
                availability = offers_list[0].get('availability', '')
                in_stock = 'InStock' in availability
            
            brand = data.get('brand')
            if isinstance(brand, dict):
                brand = brand.get('name')
            
            return {
                'supermarket': self.supermarket,
                'name': data.get('name'),
                'price': price,
                'original_price': list_price,
                'brand': brand,
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
            logger.error(f"Error parsing product data: {e}")
            return None
