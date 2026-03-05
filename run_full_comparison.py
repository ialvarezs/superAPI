"""
Final comparison script - Match Tienda products in other stores
"""
import json
from scrapers.base_scraper import BaseScraper  
from config import SUPERMARKETS
from product_matcher import ProductMatcher
from database import ProductDatabase
import pandas as pd

print("\n" + "="*80)
print("FULL SUPERMARKET COMPARISON")
print("="*80)

# Load Tienda products
print("\n📦 Loading Tienda Inglesa products...")
with open('data/tienda_final_products.json', 'r', encoding='utf-8') as f:
    tienda_products = json.load(f)

print(f"   ✅ Loaded {len(tienda_products)} products from Tienda Inglesa")

# Scrape Disco
print("\n🛒 Scraping Disco...")
disco_scraper = BaseScraper(SUPERMARKETS['disco'])
disco_products = disco_scraper.run_scraping()
print(f"   ✅ Found {len(disco_products)} products from Disco")

# Scrape Devoto
print("\n🛒 Scraping Devoto...")
devoto_scraper = BaseScraper(SUPERMARKETS['devoto'])
devoto_products = devoto_scraper.run_scraping()
print(f"   ✅ Found {len(devoto_products)} products from Devoto")

# Combine all
all_products = tienda_products + disco_products + devoto_products
print(f"\n✅ Total products: {len(all_products)}")

# Save all products
with open('data/all_products_final.json', 'w', encoding='utf-8') as f:
    json.dump(all_products, f, ensure_ascii=False, indent=2)

# Match products
print("\n🔗 Matching products across stores...")
matcher = ProductMatcher()
matches = matcher.find_matches(all_products)

print(f"   ✅ Found {len(matches)} product matches")

# Filter matches with Tienda
tienda_matches = [m for m in matches if any(p['supermarket'] == 'Tienda Inglesa' for p in m['products']) and len(m['products']) > 1]
print(f"   ✅ Matches with Tienda Inglesa: {len(tienda_matches)}")

# Save matches
with open('results/final_matches.json', 'w', encoding='utf-8') as f:
    json.dump(tienda_matches, f, ensure_ascii=False, indent=2)

# Create comparison report
print("\n📊 Creating price comparison report...")
comparison_data = []

for match in tienda_matches:
    tienda_prod = next((p for p in match['products'] if p['supermarket'] == 'Tienda Inglesa'), None)
    
    if not tienda_prod:
        continue
    
    for other_prod in match['products']:
        if other_prod['supermarket'] == 'Tienda Inglesa':
            continue
        
        t_price = tienda_prod.get('price')
        o_price = other_prod.get('price')
        
        if t_price and o_price:
            diff = o_price - t_price
            pct = (abs(diff) / t_price) * 100
            cheaper = 'Tienda Inglesa' if t_price < o_price else other_prod['supermarket']
            
            comparison_data.append({
                'Product': match['matched_name'],
                'Tienda_Price': f"${t_price:.0f}",
                f"{other_prod['supermarket']}_Price": f"${o_price:.0f}",
                'Difference': f"${abs(diff):.0f}",
                'Percentage': f"{pct:.1f}%",
                'Cheaper_At': cheaper,
                'Tienda_Barcode': tienda_prod.get('barcode', 'N/A'),
                'Match_Score': match.get('score', 0)
            })

if comparison_data:
    df = pd.DataFrame(comparison_data)
    df = df.sort_values('Difference', key=lambda x: x.str.replace('$', '').astype(float), ascending=False)
    
    df.to_csv('results/final_price_comparison.csv', index=False)
    
    print(f"   ✅ Comparison report saved: results/final_price_comparison.csv")
    print(f"\n💰 TOP 10 PRICE DIFFERENCES:")
    print("-"*80)
    for idx, row in df.head(10).iterrows():
        print(f"\n{idx+1}. {row['Product'][:60]}")
        print(f"   Tienda: {row['Tienda_Price']} | Other: {list(row.items())[2][1]}")
        print(f"   Difference: {row['Difference']} ({row['Percentage']}) - Cheaper at {row['Cheaper_At']}")
else:
    print("   ⚠️  No price comparisons available")

# Save to database
print("\n💾 Saving to database...")
db = ProductDatabase('data/final_comparison.db')
for product in all_products:
    db.insert_product(product)

print(f"   ✅ Database saved: data/final_comparison.db")

print("\n" + "="*80)
print("COMPARISON COMPLETE!")
print("="*80)
print(f"\n📊 Summary:")
print(f"   • Tienda Inglesa: {len(tienda_products)} products")
print(f"   • Disco: {len(disco_products)} products")
print(f"   • Devoto: {len(devoto_products)} products")
print(f"   • Total: {len(all_products)} products")
print(f"   • Matches: {len(tienda_matches)} products found in multiple stores")
print(f"\n📁 Output files:")
print(f"   • data/all_products_final.json")
print(f"   • results/final_matches.json")
print(f"   • results/final_price_comparison.csv")
print(f"   • data/final_comparison.db")

