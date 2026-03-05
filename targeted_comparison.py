"""
Targeted Comparison Strategy:
1. Scrape 200 products from Tienda Inglesa (base)
2. Use those products to search in Disco and Devoto
3. Match and compare prices

This approach maximizes comparison coverage by using Tienda Inglesa as the source of truth.
"""
import json
import time
from typing import List, Dict
from tienda_inglesa_production_scraper import TiendaInglesaScraper
from scrapers.base_scraper import BaseScraper
from config import SUPERMARKETS
from product_matcher import ProductMatcher
from database import ProductDatabase
import pandas as pd


class TargetedComparisonRunner:
    """
    Scrape Tienda Inglesa first, then search for those products in other stores
    """
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.tienda_products = []
        self.disco_products = []
        self.devoto_products = []
        self.all_products = []
        self.matches = []
    
    def scrape_tienda_inglesa_base(self, target_products: int = 200):
        """Step 1: Scrape 200 products from Tienda Inglesa as base"""
        print("\n" + "="*80)
        print("STEP 1: SCRAPING TIENDA INGLESA (BASE)")
        print("="*80)
        print(f"Target: {target_products} dairy products\n")
        
        scraper = TiendaInglesaScraper(
            headless=self.headless,
            max_products=target_products
        )
        
        # Use hybrid strategy for maximum coverage
        self.tienda_products = scraper.scrape_with_strategy(strategy='hybrid')
        scraper.save_results('tienda_base_200')
        
        print(f"\n✅ Tienda Inglesa: {len(self.tienda_products)} products scraped")
        
        return self.tienda_products
    
    def search_in_disco(self, search_terms: List[str]):
        """Step 2: Search for Tienda products in Disco"""
        print("\n" + "="*80)
        print("STEP 2: SEARCHING IN DISCO")
        print("="*80)
        print(f"Searching for {len(search_terms)} terms from Tienda Inglesa\n")
        
        # Use the base scraper for now
        # TODO: Implement targeted search scraper for Disco
        scraper = BaseScraper(SUPERMARKETS['disco'])
        self.disco_products = scraper.run_scraping()
        
        print(f"\n✅ Disco: {len(self.disco_products)} products found")
        
        return self.disco_products
    
    def search_in_devoto(self, search_terms: List[str]):
        """Step 3: Search for Tienda products in Devoto"""
        print("\n" + "="*80)
        print("STEP 3: SEARCHING IN DEVOTO")
        print("="*80)
        print(f"Searching for {len(search_terms)} terms from Tienda Inglesa\n")
        
        # Use the base scraper for now
        # TODO: Implement targeted search scraper for Devoto
        scraper = BaseScraper(SUPERMARKETS['devoto'])
        self.devoto_products = scraper.run_scraping()
        
        print(f"\n✅ Devoto: {len(self.devoto_products)} products found")
        
        return self.devoto_products
    
    def extract_search_terms(self, products: List[Dict], max_terms: int = 50) -> List[str]:
        """
        Extract key search terms from Tienda products
        Focus on brands and product types for targeted searching
        """
        search_terms = set()
        
        for product in products:
            name = product.get('name', '')
            brand = product.get('brand', '')
            
            # Add brand
            if brand:
                search_terms.add(brand.lower())
            
            # Extract key product terms
            name_lower = name.lower()
            
            # Common dairy products
            if 'leche' in name_lower:
                search_terms.add('leche')
            if 'yogur' in name_lower:
                search_terms.add('yogur')
            if 'queso' in name_lower:
                search_terms.add('queso')
            if 'manteca' in name_lower:
                search_terms.add('manteca')
            if 'dulce de leche' in name_lower:
                search_terms.add('dulce de leche')
            if 'crema' in name_lower:
                search_terms.add('crema')
        
        # Return top terms
        return list(search_terms)[:max_terms]
    
    def match_products(self):
        """Step 4: Match products across all stores"""
        print("\n" + "="*80)
        print("STEP 4: MATCHING PRODUCTS ACROSS STORES")
        print("="*80)
        
        # Combine all products
        self.all_products = self.tienda_products + self.disco_products + self.devoto_products
        print(f"Total products to match: {len(self.all_products)}")
        
        # Use product matcher
        matcher = ProductMatcher()
        self.matches = matcher.find_matches(self.all_products)
        
        print(f"\n✅ Found {len(self.matches)} product matches\n")
        
        # Filter to only matches with Tienda Inglesa
        tienda_matches = []
        for match in self.matches:
            stores = [p['supermarket'] for p in match['products']]
            if 'Tienda Inglesa' in stores and len(stores) > 1:
                tienda_matches.append(match)
        
        print(f"✅ Matches including Tienda Inglesa: {len(tienda_matches)}")
        
        return tienda_matches
    
    def create_comparison_report(self, matches: List[Dict]):
        """Step 5: Create detailed comparison report"""
        print("\n" + "="*80)
        print("STEP 5: CREATING COMPARISON REPORT")
        print("="*80)
        
        comparison_data = []
        
        for match in matches:
            products = match['products']
            
            # Find Tienda Inglesa product
            tienda_product = next((p for p in products if p['supermarket'] == 'Tienda Inglesa'), None)
            if not tienda_product:
                continue
            
            # Compare with each other store
            for other_product in products:
                if other_product['supermarket'] == 'Tienda Inglesa':
                    continue
                
                tienda_price = tienda_product.get('price')
                other_price = other_product.get('price')
                
                if tienda_price and other_price:
                    diff = other_price - tienda_price
                    pct = (abs(diff) / tienda_price) * 100
                    cheaper_store = 'Tienda Inglesa' if tienda_price < other_price else other_product['supermarket']
                    savings = abs(diff)
                    
                    comparison_data.append({
                        'Product_Name': match['matched_name'],
                        'Tienda_Inglesa_Price': f"${tienda_price:.0f}",
                        f"{other_product['supermarket']}_Price": f"${other_price:.0f}",
                        'Price_Difference': f"${diff:.0f}",
                        'Percentage_Diff': f"{pct:.1f}%",
                        'Cheaper_At': cheaper_store,
                        'Savings': f"${savings:.0f}",
                        'Tienda_URL': tienda_product.get('url', ''),
                        'Other_Store': other_product['supermarket']
                    })
        
        if not comparison_data:
            print("⚠️  No price comparisons available")
            return None
        
        # Create DataFrame and sort by savings
        df = pd.DataFrame(comparison_data)
        df = df.sort_values('Savings', ascending=False, key=lambda x: x.str.replace('$', '').astype(float))
        
        # Save to CSV
        df.to_csv('results/tienda_base_comparison.csv', index=False)
        
        # Save to JSON
        with open('results/tienda_base_comparison.json', 'w', encoding='utf-8') as f:
            json.dump(comparison_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Comparison report saved:")
        print(f"   • results/tienda_base_comparison.csv")
        print(f"   • results/tienda_base_comparison.json")
        
        # Display top 10 best deals
        print(f"\n💰 TOP 10 BEST DEALS:")
        print("-" * 80)
        for idx, row in df.head(10).iterrows():
            print(f"\n{idx+1}. {row['Product_Name']}")
            print(f"   Tienda Inglesa: {row['Tienda_Inglesa_Price']}")
            other_store = row['Other_Store']
            other_price_col = f"{other_store}_Price"
            print(f"   {other_store}: {row[other_price_col]}")
            print(f"   💵 Save {row['Savings']} ({row['Percentage_Diff']}) at {row['Cheaper_At']}")
        
        return df
    
    def save_all_data(self):
        """Save all collected data"""
        print("\n" + "="*80)
        print("SAVING ALL DATA")
        print("="*80)
        
        # Save all products
        all_data = {
            'tienda_inglesa': self.tienda_products,
            'disco': self.disco_products,
            'devoto': self.devoto_products
        }
        
        with open('data/tienda_base_all_products.json', 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
        
        # Save matches
        with open('results/tienda_base_matches.json', 'w', encoding='utf-8') as f:
            json.dump(self.matches, f, ensure_ascii=False, indent=2)
        
        # Save to database
        try:
            db = ProductDatabase('data/tienda_base_comparison.db')
            for product in self.all_products:
                db.insert_product(product)
            print(f"✅ Database saved: data/tienda_base_comparison.db")
        except Exception as e:
            print(f"⚠️  Database save failed: {e}")
        
        print(f"✅ All data saved")
    
    def run_targeted_comparison(self, target_products: int = 200):
        """
        Main method: Run the full targeted comparison
        
        Strategy:
        1. Scrape 200 products from Tienda Inglesa
        2. Extract search terms
        3. Search for those products in Disco and Devoto
        4. Match and compare
        5. Generate report
        """
        print("\n" + "🎯"*40)
        print("TARGETED COMPARISON STRATEGY")
        print("Base: Tienda Inglesa → Search in Disco & Devoto")
        print("🎯"*40)
        
        start_time = time.time()
        
        # Step 1: Scrape Tienda Inglesa
        self.scrape_tienda_inglesa_base(target_products)
        
        if not self.tienda_products:
            print("❌ No products from Tienda Inglesa. Aborting.")
            return
        
        # Step 2 & 3: Search in other stores
        search_terms = self.extract_search_terms(self.tienda_products)
        print(f"\n🔍 Key search terms extracted: {len(search_terms)}")
        print(f"   {', '.join(search_terms[:10])}{'...' if len(search_terms) > 10 else ''}")
        
        print("\n⏳ Waiting 5 seconds before searching other stores...")
        time.sleep(5)
        
        self.search_in_disco(search_terms)
        
        print("\n⏳ Waiting 5 seconds before next store...")
        time.sleep(5)
        
        self.search_in_devoto(search_terms)
        
        # Step 4: Match products
        tienda_matches = self.match_products()
        
        # Step 5: Create report
        if tienda_matches:
            self.create_comparison_report(tienda_matches)
        
        # Save everything
        self.save_all_data()
        
        # Summary
        elapsed = time.time() - start_time
        print("\n" + "="*80)
        print("📊 FINAL SUMMARY")
        print("="*80)
        print(f"\n⏱️  Total time: {elapsed/60:.1f} minutes")
        print(f"\n📦 Products scraped:")
        print(f"   • Tienda Inglesa: {len(self.tienda_products)}")
        print(f"   • Disco:          {len(self.disco_products)}")
        print(f"   • Devoto:         {len(self.devoto_products)}")
        print(f"   • TOTAL:          {len(self.all_products)}")
        print(f"\n🔗 Matches found:")
        print(f"   • Total matches:           {len(self.matches)}")
        print(f"   • With Tienda Inglesa:     {len([m for m in self.matches if any(p['supermarket'] == 'Tienda Inglesa' for p in m['products'])])}")
        print(f"   • Price comparisons ready: {len([m for m in self.matches if len(m['products']) > 1])}")
        
        print(f"\n📁 Output files:")
        print(f"   • results/tienda_base_comparison.csv")
        print(f"   • results/tienda_base_comparison.json")
        print(f"   • data/tienda_base_all_products.json")
        print(f"   • data/tienda_base_comparison.db")
        
        print(f"\n✅ TARGETED COMPARISON COMPLETE!")
        
        return self.all_products, tienda_matches


def main():
    """Run the targeted comparison"""
    print("\n🛒 URUGUAY SUPERMARKET TARGETED COMPARISON")
    print("=" * 80)
    print("\nStrategy:")
    print("  1. Scrape 200 products from Tienda Inglesa (base)")
    print("  2. Search for those products in Disco and Devoto")
    print("  3. Match and compare prices")
    print("\nEstimated time: 15-20 minutes")
    print("\nPress Ctrl+C to cancel or wait 5 seconds to start...")
    
    time.sleep(5)
    
    # Create runner
    runner = TargetedComparisonRunner(headless=False)
    
    # Run targeted comparison
    products, matches = runner.run_targeted_comparison(target_products=200)
    
    print("\n" + "🎉"*40)
    print("READY FOR ANALYSIS!")
    print("🎉"*40)
    print("\nNext steps:")
    print("  1. Open: results/tienda_base_comparison.csv")
    print("  2. Review: Best deals and price differences")
    print("  3. Query: data/tienda_base_comparison.db")
    print()
    
    return runner


if __name__ == "__main__":
    runner = main()
