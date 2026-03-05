"""
Data analysis and visualization tools for supermarket scraping results
"""
import pandas as pd
from typing import List, Dict
import numpy as np
from database import ProductDatabase
import json

# Optional imports for visualization
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


class SupermarketAnalyzer:
    def __init__(self, db_path: str = "data/products.db"):
        self.db = ProductDatabase(db_path)

    def analyze_price_differences(self) -> pd.DataFrame:
        """Analyze price differences across supermarkets"""
        matches = self.db.get_matches()

        if not matches:
            print("No matches found for price analysis")
            return pd.DataFrame()

        df = pd.DataFrame(matches)

        # Filter matches with valid prices
        df = df[(df['price_1'].notna()) & (df['price_2'].notna())]

        if len(df) == 0:
            print("No matches with valid prices found")
            return pd.DataFrame()

        # Calculate price difference percentage
        df['price_diff_pct'] = (
            abs(df['price_1'] - df['price_2']) /
            ((df['price_1'] + df['price_2']) / 2) * 100
        )

        return df

    def find_best_deals(self, min_price_difference: float = 5.0) -> List[Dict]:
        """Find products with significant price differences"""
        df = self.analyze_price_differences()

        if len(df) == 0:
            return []

        # Filter for significant differences
        significant_deals = df[df['price_diff_pct'] >= min_price_difference].copy()

        # Sort by price difference percentage
        significant_deals = significant_deals.sort_values('price_diff_pct', ascending=False)

        deals = []
        for _, row in significant_deals.iterrows():
            deal = {
                'product_name_1': row['name_1'],
                'product_name_2': row['name_2'],
                'store_1': row['supermarket_1'],
                'store_2': row['supermarket_2'],
                'price_1': row['price_1'],
                'price_2': row['price_2'],
                'savings': abs(row['price_1'] - row['price_2']),
                'savings_percentage': row['price_diff_pct'],
                'cheaper_store': row['cheaper_store'],
                'similarity_score': row['similarity_score']
            }
            deals.append(deal)

        return deals

    def store_comparison_summary(self) -> Dict:
        """Generate summary comparison across stores"""
        products = self.db.get_products()

        if not products:
            return {}

        df = pd.DataFrame(products)

        # Filter products with prices
        df_priced = df[df['price'].notna()].copy()

        summary = {}

        for store in df['supermarket'].unique():
            store_df = df_priced[df_priced['supermarket'] == store]

            if len(store_df) > 0:
                summary[store] = {
                    'total_products': len(df[df['supermarket'] == store]),
                    'products_with_prices': len(store_df),
                    'average_price': float(store_df['price'].mean()),
                    'median_price': float(store_df['price'].median()),
                    'min_price': float(store_df['price'].min()),
                    'max_price': float(store_df['price'].max()),
                    'products_with_barcodes': len(store_df[store_df['barcode'].notna()])
                }

        return summary

    def brand_analysis(self) -> Dict:
        """Analyze brand distribution across stores"""
        products = self.db.get_products()

        if not products:
            return {}

        df = pd.DataFrame(products)

        # Extract brands (simple approach - first word)
        df['extracted_brand'] = df['name'].str.split().str[0].str.title()

        brand_analysis = {}

        for store in df['supermarket'].unique():
            store_df = df[df['supermarket'] == store]
            brand_counts = store_df['extracted_brand'].value_counts().head(10)

            brand_analysis[store] = {
                'top_brands': brand_counts.to_dict(),
                'unique_brands': len(store_df['extracted_brand'].unique())
            }

        return brand_analysis

    def generate_report(self, output_file: str = "results/analysis_report.json"):
        """Generate comprehensive analysis report"""
        import os
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        report = {
            'generated_at': pd.Timestamp.now().isoformat(),
            'database_stats': self.db.get_statistics(),
            'store_comparison': self.store_comparison_summary(),
            'brand_analysis': self.brand_analysis(),
            'best_deals': self.find_best_deals(),
            'price_analysis': {}
        }

        # Price difference analysis
        price_df = self.analyze_price_differences()
        if len(price_df) > 0:
            report['price_analysis'] = {
                'total_matches': len(price_df),
                'average_price_difference_pct': float(price_df['price_diff_pct'].mean()),
                'max_price_difference_pct': float(price_df['price_diff_pct'].max()),
                'matches_with_significant_difference': len(price_df[price_df['price_diff_pct'] >= 10])
            }

        # Save report
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)

        print(f"Analysis report saved to {output_file}")

        # Print summary to console
        self.print_summary(report)

        return report

    def print_summary(self, report: Dict):
        """Print analysis summary to console"""
        print("\n" + "="*60)
        print("🔍 SUPERMARKET ANALYSIS SUMMARY")
        print("="*60)

        # Database stats
        stats = report['database_stats']
        print(f"\n📊 DATABASE STATISTICS")
        print("-" * 30)
        print(f"Total products: {stats['total_products']}")
        print(f"Products with barcodes: {stats['products_with_barcodes']}")
        print(f"Total matches found: {stats['total_matches']}")

        print(f"\nProducts by store:")
        for store, count in stats['products_by_store'].items():
            print(f"  • {store}: {count} products")

        # Store comparison
        comparison = report['store_comparison']
        if comparison:
            print(f"\n💰 PRICE COMPARISON")
            print("-" * 30)
            for store, data in comparison.items():
                print(f"{store}:")
                print(f"  • Products with prices: {data['products_with_prices']}")
                print(f"  • Average price: ${data['average_price']:.2f}")
                print(f"  • Price range: ${data['min_price']:.2f} - ${data['max_price']:.2f}")

        # Best deals
        deals = report['best_deals']
        if deals:
            print(f"\n🎯 BEST DEALS FOUND ({len(deals)} deals with >5% difference)")
            print("-" * 50)
            for i, deal in enumerate(deals[:5]):  # Show top 5
                print(f"{i+1}. {deal['product_name_1'][:50]}...")
                print(f"   {deal['store_1']}: ${deal['price_1']:.2f}")
                print(f"   {deal['store_2']}: ${deal['price_2']:.2f}")
                print(f"   💸 Save ${deal['savings']:.2f} ({deal['savings_percentage']:.1f}%) at {deal['cheaper_store']}")
                print()

        # Price analysis
        price_analysis = report['price_analysis']
        if price_analysis:
            print(f"📈 PRICE MATCHING ANALYSIS")
            print("-" * 30)
            print(f"Product matches analyzed: {price_analysis['total_matches']}")
            print(f"Average price difference: {price_analysis['average_price_difference_pct']:.1f}%")
            print(f"Matches with >10% difference: {price_analysis['matches_with_significant_difference']}")

        print("\n" + "="*60)

    def export_deals_csv(self, output_file: str = "results/best_deals.csv"):
        """Export best deals to CSV"""
        deals = self.find_best_deals()

        if not deals:
            print("No deals found to export")
            return

        df = pd.DataFrame(deals)
        df.to_csv(output_file, index=False)
        print(f"Best deals exported to {output_file}")

    def create_visualizations(self, output_dir: str = "results/plots"):
        """Create visualization plots (requires matplotlib)"""
        import os
        os.makedirs(output_dir, exist_ok=True)

        if not HAS_MATPLOTLIB:
            print("Matplotlib not available. Skipping visualizations.")
            return

        try:
            # Price distribution by store
            products = self.db.get_products()
            if products:
                df = pd.DataFrame(products)
                df_priced = df[df['price'].notna()]

                if len(df_priced) > 0:
                    plt.figure(figsize=(12, 6))
                    sns.boxplot(data=df_priced, x='supermarket', y='price')
                    plt.title('Price Distribution by Supermarket')
                    plt.xticks(rotation=45)
                    plt.tight_layout()
                    plt.savefig(f"{output_dir}/price_distribution.png")
                    plt.close()

            # Price differences
            price_df = self.analyze_price_differences()
            if len(price_df) > 0:
                plt.figure(figsize=(10, 6))
                plt.hist(price_df['price_diff_pct'], bins=20, edgecolor='black')
                plt.title('Distribution of Price Differences (%)')
                plt.xlabel('Price Difference (%)')
                plt.ylabel('Number of Products')
                plt.tight_layout()
                plt.savefig(f"{output_dir}/price_differences.png")
                plt.close()

            print(f"Visualizations saved to {output_dir}/")

        except Exception as e:
            print(f"Error creating visualizations: {e}")


if __name__ == "__main__":
    analyzer = SupermarketAnalyzer()
    analyzer.generate_report()
    analyzer.export_deals_csv()
    analyzer.create_visualizations()