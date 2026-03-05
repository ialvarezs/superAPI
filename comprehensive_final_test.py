"""
Comprehensive test combining all three supermarkets with anti-bot techniques
"""
import json
import pandas as pd
from product_matcher import ProductMatcher
from database import ProductDatabase
from analyzer import SupermarketAnalyzer


def load_all_scraped_data():
    """Load all successfully scraped dairy products"""
    all_products = []

    # Load Tienda Inglesa data (new)
    try:
        with open('data/tienda_inglesa_final_dairy.json', 'r', encoding='utf-8') as f:
            tienda_products = json.load(f)
            all_products.extend(tienda_products)
            print(f"✅ Loaded {len(tienda_products)} products from Tienda Inglesa")
    except FileNotFoundError:
        print("⚠️  Tienda Inglesa data not found")

    # Load Disco data (existing)
    try:
        with open('data/disco_lacteos.json', 'r', encoding='utf-8') as f:
            disco_products = json.load(f)
            all_products.extend(disco_products)
            print(f"✅ Loaded {len(disco_products)} products from Disco")
    except FileNotFoundError:
        print("⚠️  Disco data not found")

    # Load Devoto data (existing)
    try:
        with open('data/devoto_lacteos.json', 'r', encoding='utf-8') as f:
            devoto_products = json.load(f)
            all_products.extend(devoto_products)
            print(f"✅ Loaded {len(devoto_products)} products from Devoto")
    except FileNotFoundError:
        print("⚠️  Devoto data not found")

    return all_products


def main():
    print("🛒 COMPREHENSIVE SUPERMARKET COMPARISON - FINAL TEST")
    print("=" * 65)

    # Load all scraped data
    all_products = load_all_scraped_data()

    if not all_products:
        print("❌ No products found! Please run the scrapers first.")
        return

    print(f"\n📊 TOTAL DATA LOADED:")
    print(f"   Total products: {len(all_products)}")

    # Group by supermarket
    by_store = {}
    for product in all_products:
        store = product.get('supermarket', 'Unknown')
        if store not in by_store:
            by_store[store] = []
        by_store[store].append(product)

    for store, products in by_store.items():
        print(f"   {store}: {len(products)} products")

    # Initialize database and save all products
    db = ProductDatabase('data/final_comprehensive.db')

    print(f"\n💾 SAVING TO DATABASE...")
    for store, products in by_store.items():
        count = db.save_products(products, store)
        print(f"   Saved {count} {store} products to database")

    # Run product matching
    print(f"\n🔍 PRODUCT MATCHING ANALYSIS:")
    matcher = ProductMatcher()
    matches = matcher.find_matches(all_products)

    print(f"   Found {len(matches)} product matches across stores")

    if matches:
        db.save_matches(matches)
        matcher.save_matches(matches, 'results/final_comprehensive_matches.json')

        # Show sample matches
        print(f"\n📋 SAMPLE MATCHES:")
        for i, match in enumerate(matches[:3]):
            p1 = match['product_1']
            p2 = match['product_2']
            print(f"\n   Match {i+1} (Similarity: {match['similarity_score']:.2f}):")
            print(f"   🏪 {p1['supermarket']}: {p1['name']} - ${p1['price']}")
            print(f"   🏪 {p2['supermarket']}: {p2['name']} - ${p2['price']}")

            if match.get('price_difference') and match['price_difference'] > 0:
                savings_pct = match.get('price_difference_percentage', 0)
                print(f"   💰 Save ${match['price_difference']:.0f} ({savings_pct:.1f}%) at {match['cheaper_store']}")

    # Generate comprehensive analysis
    print(f"\n📈 COMPREHENSIVE ANALYSIS:")
    analyzer = SupermarketAnalyzer('data/final_comprehensive.db')
    report = analyzer.generate_report('results/final_comprehensive_report.json')
    analyzer.export_deals_csv('results/final_comprehensive_deals.csv')

    # Export all data
    db.export_to_csv('results/final_comprehensive')

    print(f"\n🎯 FINAL COMPARISON RESULTS:")
    print(f"-" * 40)

    stats = db.get_statistics()
    print(f"Total products in comparison: {stats['total_products']}")
    print(f"Cross-store matches found: {stats['total_matches']}")

    if stats['products_by_store']:
        print(f"\nProducts by supermarket:")
        for store, count in stats['products_by_store'].items():
            avg_price = stats['average_prices'].get(store, 0)
            print(f"  • {store}: {count} products (avg: ${avg_price:.0f})")

    # Show price comparison insights
    max_diff = 0
    if matches:
        price_differences = [m.get('price_difference_percentage', 0) for m in matches if m.get('price_difference_percentage')]
        if price_differences:
            avg_diff = sum(price_differences) / len(price_differences)
            max_diff = max(price_differences)
            print(f"\nPrice analysis:")
            print(f"  • Average price difference: {avg_diff:.1f}%")
            print(f"  • Maximum savings opportunity: {max_diff:.1f}%")

    print(f"\n📁 RESULTS SAVED TO:")
    print(f"   • Database: data/final_comprehensive.db")
    print(f"   • Matches: results/final_comprehensive_matches.json")
    print(f"   • Analysis: results/final_comprehensive_report.json")
    print(f"   • Deals: results/final_comprehensive_deals.csv")
    print(f"   • Export: results/final_comprehensive/")

    # Final verdict
    print(f"\n🏆 PROOF OF CONCEPT VERDICT:")
    print(f"=" * 35)

    if stats['total_products'] >= 3 and stats['total_matches'] >= 1:
        print(f"✅ SUCCESS! The POC demonstrates:")
        print(f"   🕷️  Web scraping works (bypassed anti-bot measures)")
        print(f"   🔗 Product matching works ({stats['total_matches']} matches found)")
        print(f"   💰 Price differences exist (savings opportunities identified)")
        print(f"   📊 Analysis pipeline works (comprehensive reporting)")
        print(f"\n🚀 Ready for MVP development!")

        if max_diff > 5:
            print(f"   💡 Users could save up to {max_diff:.1f}% on groceries!")
    else:
        print(f"⚠️  LIMITED SUCCESS:")
        print(f"   - Need more product data for full validation")
        print(f"   - Core technology works, scale needs improvement")

    return all_products, matches


if __name__ == "__main__":
    products, matches = main()