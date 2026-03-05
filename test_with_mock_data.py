"""
Test the product matching system with mock lacteos data
to better demonstrate the capabilities
"""
from product_matcher import ProductMatcher
from database import ProductDatabase
from analyzer import SupermarketAnalyzer
import json

def create_mock_lacteos_data():
    """Create realistic mock dairy products data"""
    mock_products = [
        # Tienda Inglesa products
        {
            'supermarket': 'Tienda Inglesa',
            'name': 'Leche Conaprole Entera 1L',
            'price': 95.0,
            'barcode': '7730894000123',
            'brand': 'Conaprole',
            'image_url': 'https://example.com/conaprole-1l.jpg',
            'url': 'https://tiendainglesa.com/product/1'
        },
        {
            'supermarket': 'Tienda Inglesa',
            'name': 'Yogurt Conaprole Natural 1kg',
            'price': 180.0,
            'barcode': '7730894000456',
            'brand': 'Conaprole'
        },
        {
            'supermarket': 'Tienda Inglesa',
            'name': 'Dulce de Leche La Serenísima 400g',
            'price': 220.0,
            'barcode': '7790040123456',
            'brand': 'La Serenísima'
        },
        {
            'supermarket': 'Tienda Inglesa',
            'name': 'Queso Mozzarella Calcar 200g',
            'price': 165.0,
            'brand': 'Calcar'
        },

        # Disco products (some matching, some different)
        {
            'supermarket': 'Disco',
            'name': 'LECHE CONAPROLE ENTERA 1000ML',
            'price': 89.0,  # Cheaper at Disco
            'barcode': '7730894000123',  # Same barcode as Tienda Inglesa
            'brand': 'Conaprole'
        },
        {
            'supermarket': 'Disco',
            'name': 'Yogur Natural Conaprole 1 Kg',
            'price': 175.0,  # Slightly cheaper
            'barcode': '7730894000456',  # Same product
            'brand': 'Conaprole'
        },
        {
            'supermarket': 'Disco',
            'name': 'Dulce Leche Serenisima 400gr',
            'price': 235.0,  # More expensive
            'barcode': '7790040123456',  # Same product
            'brand': 'La Serenísima'
        },
        {
            'supermarket': 'Disco',
            'name': 'Queso Cremoso Sancor 300g',
            'price': 145.0,
            'brand': 'Sancor'
        },

        # Devoto products
        {
            'supermarket': 'Devoto',
            'name': 'Leche Conaprole Entera Litro',
            'price': 92.0,  # Mid-price
            'barcode': '7730894000123',  # Same product as others
            'brand': 'Conaprole'
        },
        {
            'supermarket': 'Devoto',
            'name': 'Yogurt Conaprole Natural 1000g',
            'price': 185.0,  # Most expensive
            'brand': 'Conaprole'
        },
        {
            'supermarket': 'Devoto',
            'name': 'Dulce de Leche Artesanal La Serenísima 400g',
            'price': 210.0,  # Cheapest
            'barcode': '7790040123456',
            'brand': 'La Serenísima'
        },
        {
            'supermarket': 'Devoto',
            'name': 'Manteca Presidente 200g',
            'price': 120.0,
            'brand': 'Presidente'
        }
    ]

    return mock_products

def main():
    print("🧪 TESTING PRODUCT MATCHING WITH MOCK LACTEOS DATA")
    print("=" * 60)

    # Create mock data
    mock_products = create_mock_lacteos_data()

    # Initialize database and clear existing data
    db = ProductDatabase()

    # Save mock products to database
    print("📝 Saving mock products to database...")
    for supermarket in ['Tienda Inglesa', 'Disco', 'Devoto']:
        supermarket_products = [p for p in mock_products if p['supermarket'] == supermarket]
        db.save_products(supermarket_products, supermarket)
        print(f"  • {supermarket}: {len(supermarket_products)} products")

    # Test product matching
    print(f"\n🔍 TESTING PRODUCT MATCHING")
    print("-" * 30)

    matcher = ProductMatcher()
    matches = matcher.find_matches(mock_products)

    print(f"Found {len(matches)} matches")

    # Save matches
    if matches:
        db.save_matches(matches)
        matcher.save_matches(matches, 'results/mock_product_matches.json')

        # Show some example matches
        print(f"\n📊 SAMPLE MATCHES:")
        for i, match in enumerate(matches[:3]):
            p1 = match['product_1']
            p2 = match['product_2']

            print(f"\nMatch {i+1} (Similarity: {match['similarity_score']:.2f}):")
            print(f"  {p1['supermarket']}: {p1['name']} - ${p1['price']}")
            print(f"  {p2['supermarket']}: {p2['name']} - ${p2['price']}")

            if match['price_difference'] and match['price_difference'] > 0:
                print(f"  💰 Save ${match['price_difference']:.0f} ({match.get('price_difference_percentage', 0):.1f}%) at {match['cheaper_store']}")

    # Run analysis
    print(f"\n📈 RUNNING ANALYSIS")
    print("-" * 20)

    analyzer = SupermarketAnalyzer()
    report = analyzer.generate_report('results/mock_analysis_report.json')
    analyzer.export_deals_csv('results/mock_best_deals.csv')

    # Show file contents
    print(f"\n📁 Generated files:")
    print(f"  • Mock matches: results/mock_product_matches.json")
    print(f"  • Analysis report: results/mock_analysis_report.json")
    print(f"  • Best deals: results/mock_best_deals.csv")
    print(f"  • Database: data/products.db")

if __name__ == "__main__":
    main()