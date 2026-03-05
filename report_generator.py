"""
Report generator for scraping results
"""
import json
from datetime import datetime
from typing import List, Dict
import os
from logger import setup_logger

logger = setup_logger('report_generator')

class ReportGenerator:
    """Generate reports from scraping and matching results"""
    
    def __init__(self, output_dir: str = "results"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_full_report(self, products_by_store: Dict[str, List[Dict]], 
                            matches: List[Dict], db_stats: Dict) -> str:
        """Generate comprehensive report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"{self.output_dir}/report_{timestamp}.json"
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_products': sum(len(p) for p in products_by_store.values()),
                'total_matches': len(matches),
                'supermarkets': list(products_by_store.keys()),
                'products_by_store': {store: len(prods) for store, prods in products_by_store.items()}
            },
            'database_stats': db_stats,
            'top_matches': self._get_top_matches(matches, 20),
            'best_deals': self._get_best_deals(matches, 10),
            'price_statistics': self._calculate_price_stats(products_by_store)
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Report generated: {report_file}")
        
        # Generate HTML report
        html_file = self._generate_html_report(report, timestamp)
        
        return html_file
    
    def _get_top_matches(self, matches: List[Dict], limit: int = 20) -> List[Dict]:
        """Get top matches by similarity score"""
        sorted_matches = sorted(matches, key=lambda x: x['similarity_score'], reverse=True)
        
        return [{
            'product_1_name': m['product_1']['name'],
            'product_1_store': m['product_1']['supermarket'],
            'product_1_price': m['product_1'].get('price'),
            'product_2_name': m['product_2']['name'],
            'product_2_store': m['product_2']['supermarket'],
            'product_2_price': m['product_2'].get('price'),
            'similarity': m['similarity_score'],
            'price_diff': m.get('price_difference'),
            'cheaper_store': m.get('cheaper_store')
        } for m in sorted_matches[:limit]]
    
    def _get_best_deals(self, matches: List[Dict], limit: int = 10) -> List[Dict]:
        """Get best deals by price difference"""
        deals = [m for m in matches if m.get('price_difference')]
        sorted_deals = sorted(deals, key=lambda x: x['price_difference'], reverse=True)
        
        return [{
            'product_name': m['product_1']['name'],
            'expensive_store': m['product_2']['supermarket'] if m['product_2'].get('price', 0) > m['product_1'].get('price', 0) else m['product_1']['supermarket'],
            'expensive_price': max(m['product_1'].get('price', 0), m['product_2'].get('price', 0)),
            'cheaper_store': m['cheaper_store'],
            'cheaper_price': min(m['product_1'].get('price', 0), m['product_2'].get('price', 0)),
            'savings': m['price_difference'],
            'savings_percent': m.get('savings_percentage', 0)
        } for m in sorted_deals[:limit]]
    
    def _calculate_price_stats(self, products_by_store: Dict[str, List[Dict]]) -> Dict:
        """Calculate price statistics by store"""
        stats = {}
        
        for store, products in products_by_store.items():
            prices = [p['price'] for p in products if p.get('price')]
            
            if prices:
                stats[store] = {
                    'avg_price': sum(prices) / len(prices),
                    'min_price': min(prices),
                    'max_price': max(prices),
                    'total_products_with_price': len(prices)
                }
        
        return stats
    
    def _generate_html_report(self, report: Dict, timestamp: str) -> str:
        """Generate HTML report"""
        html_file = f"{self.output_dir}/report_{timestamp}.html"
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Supermarket Comparison Report - {timestamp}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
        .stat-card {{ background: #e8f5e9; padding: 15px; border-radius: 8px; text-align: center; }}
        .stat-card h3 {{ margin: 0; color: #2e7d32; font-size: 2em; }}
        .stat-card p {{ margin: 5px 0 0 0; color: #666; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th {{ background: #4CAF50; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
        tr:hover {{ background: #f5f5f5; }}
        .price {{ font-weight: bold; color: #2e7d32; }}
        .store {{ color: #1976d2; font-weight: 500; }}
        .savings {{ background: #ffeb3b; padding: 2px 8px; border-radius: 3px; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🛒 Supermarket Price Comparison Report</h1>
        <p><strong>Generated:</strong> {report['generated_at']}</p>
        
        <h2>📊 Summary</h2>
        <div class="summary">
            <div class="stat-card">
                <h3>{report['summary']['total_products']}</h3>
                <p>Total Products</p>
            </div>
            <div class="stat-card">
                <h3>{report['summary']['total_matches']}</h3>
                <p>Product Matches</p>
            </div>
            <div class="stat-card">
                <h3>{len(report['summary']['supermarkets'])}</h3>
                <p>Supermarkets</p>
            </div>
        </div>
        
        <h2>🏪 Products by Store</h2>
        <table>
            <tr><th>Supermarket</th><th>Products</th><th>Avg Price</th></tr>
"""
        
        for store, count in report['summary']['products_by_store'].items():
            avg_price = report['price_statistics'].get(store, {}).get('avg_price', 0)
            html += f"<tr><td class='store'>{store.replace('_', ' ').title()}</td><td>{count}</td><td class='price'>${avg_price:.2f}</td></tr>\n"
        
        html += """
        </table>
        
        <h2>💰 Best Deals (Top Savings)</h2>
        <table>
            <tr><th>Product</th><th>Expensive</th><th>Price</th><th>Cheaper</th><th>Price</th><th>Savings</th></tr>
"""
        
        for deal in report['best_deals']:
            html += f"""<tr>
                <td>{deal['product_name']}</td>
                <td class='store'>{deal['expensive_store'].replace('_', ' ').title()}</td>
                <td>${deal['expensive_price']:.2f}</td>
                <td class='store'>{deal['cheaper_store'].replace('_', ' ').title()}</td>
                <td class='price'>${deal['cheaper_price']:.2f}</td>
                <td><span class='savings'>${deal['savings']:.2f} ({deal['savings_percent']:.1f}%)</span></td>
            </tr>\n"""
        
        html += """
        </table>
        
        <h2>🔗 Top Matches</h2>
        <table>
            <tr><th>Product 1</th><th>Store</th><th>Price</th><th>Product 2</th><th>Store</th><th>Price</th><th>Similarity</th></tr>
"""
        
        for match in report['top_matches'][:15]:
            html += f"""<tr>
                <td>{match['product_1_name']}</td>
                <td class='store'>{match['product_1_store'].replace('_', ' ').title()}</td>
                <td class='price'>${match.get('product_1_price', 0):.2f}</td>
                <td>{match['product_2_name']}</td>
                <td class='store'>{match['product_2_store'].replace('_', ' ').title()}</td>
                <td class='price'>${match.get('product_2_price', 0):.2f}</td>
                <td>{match['similarity']:.2%}</td>
            </tr>\n"""
        
        html += """
        </table>
    </div>
</body>
</html>
"""
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        logger.info(f"HTML report generated: {html_file}")
        return html_file
