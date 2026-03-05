"""
Product matching logic to identify same products across different supermarkets
"""
import re
import json
import pandas as pd
from typing import List, Dict, Tuple, Optional
from fuzzywuzzy import fuzz, process
from unidecode import unidecode
from collections import defaultdict
import itertools


class ProductMatcher:
    def __init__(self, similarity_threshold: float = 0.80):
        self.similarity_threshold = similarity_threshold

        # Common brand patterns in Uruguay
        self.brand_patterns = {
            'conaprole': r'\b(conaprole|cona)\b',
            'parmalat': r'\bparmalat\b',
            'calcar': r'\bcalcar\b',
            'pilot': r'\bpilot\b',
            'la_serenisima': r'\b(la\s*serenísima|serenisima)\b',
            'sancor': r'\bsancor\b',
            'talar': r'\btalar\b',
            'milky': r'\bmilky\b',
            'claldy': r'\bclaldy\b'
        }

        # Size/volume patterns
        self.size_patterns = [
            r'(\d+(?:\.\d+)?)\s*(ml|l|cc|litros?)',
            r'(\d+(?:\.\d+)?)\s*(g|gr|kg|gramos?|kilos?)',
            r'(\d+)\s*x\s*(\d+(?:\.\d+)?)\s*(ml|l|g|gr)',
            r'pack\s*(\d+)',
            r'(\d+)\s*unidades?'
        ]

    def normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        if not text:
            return ""

        text = text.lower().strip()
        text = unidecode(text)  # Remove accents
        text = re.sub(r'[^\w\s]', ' ', text)  # Remove punctuation
        text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single
        return text.strip()

    def extract_brand(self, product_name: str) -> Optional[str]:
        """Extract brand from product name"""
        normalized_name = self.normalize_text(product_name)

        for brand, pattern in self.brand_patterns.items():
            if re.search(pattern, normalized_name, re.IGNORECASE):
                return brand.replace('_', ' ').title()

        # Try to extract first word as potential brand
        words = normalized_name.split()
        if words and len(words[0]) > 2:
            return words[0].title()

        return None

    def extract_size_info(self, product_name: str) -> Dict[str, str]:
        """Extract size/volume information"""
        size_info = {'volume': None, 'weight': None, 'quantity': None}

        for pattern in self.size_patterns:
            match = re.search(pattern, product_name, re.IGNORECASE)
            if match:
                if 'ml' in match.group().lower() or 'l' in match.group().lower() or 'cc' in match.group().lower():
                    size_info['volume'] = match.group()
                elif 'g' in match.group().lower() or 'kg' in match.group().lower():
                    size_info['weight'] = match.group()
                elif 'pack' in match.group().lower() or 'unidad' in match.group().lower():
                    size_info['quantity'] = match.group()

        return size_info

    def clean_product_name(self, name: str) -> str:
        """Clean product name for matching"""
        if not name:
            return ""

        name = self.normalize_text(name)

        # Remove size information
        for pattern in self.size_patterns:
            name = re.sub(pattern, '', name, flags=re.IGNORECASE)

        # Remove common supermarket-specific words
        remove_words = [
            'oferta', 'descuento', 'promo', 'promocion', 'especial',
            'nuevo', 'fresh', 'fresco', 'premium', 'select'
        ]

        for word in remove_words:
            name = re.sub(rf'\b{word}\b', '', name, flags=re.IGNORECASE)

        # Clean up
        name = re.sub(r'\s+', ' ', name).strip()
        return name

    def calculate_similarity(self, product1: Dict, product2: Dict) -> float:
        """Calculate similarity score between two products"""
        if product1['supermarket'] == product2['supermarket']:
            return 0.0  # Same supermarket

        # Check barcode match first (highest confidence)
        if (product1.get('barcode') and product2.get('barcode') and
                product1['barcode'] == product2['barcode']):
            return 1.0

        # Clean names for comparison
        name1 = self.clean_product_name(product1.get('name', ''))
        name2 = self.clean_product_name(product2.get('name', ''))

        if not name1 or not name2:
            return 0.0

        # Calculate different similarity metrics
        token_sort_ratio = fuzz.token_sort_ratio(name1, name2) / 100.0
        token_set_ratio = fuzz.token_set_ratio(name1, name2) / 100.0
        ratio = fuzz.ratio(name1, name2) / 100.0

        # Brand matching bonus
        brand1 = self.extract_brand(product1.get('name', ''))
        brand2 = self.extract_brand(product2.get('name', ''))

        brand_bonus = 0.0
        if brand1 and brand2:
            if brand1.lower() == brand2.lower():
                brand_bonus = 0.2
            elif fuzz.ratio(brand1.lower(), brand2.lower()) > 80:
                brand_bonus = 0.1

        # Size matching bonus
        size1 = self.extract_size_info(product1.get('name', ''))
        size2 = self.extract_size_info(product2.get('name', ''))

        size_bonus = 0.0
        for key in ['volume', 'weight', 'quantity']:
            if size1.get(key) and size2.get(key):
                if self.normalize_text(size1[key]) == self.normalize_text(size2[key]):
                    size_bonus += 0.1

        # Combined similarity score
        similarity = max(token_sort_ratio, token_set_ratio, ratio) + brand_bonus + size_bonus

        return min(similarity, 1.0)

    def find_matches(self, products: List[Dict]) -> List[Dict]:
        """Find matching products across supermarkets"""
        matches = []

        # Group products by supermarket
        by_supermarket = defaultdict(list)
        for product in products:
            if product.get('name') and product.get('supermarket'):
                by_supermarket[product['supermarket']].append(product)

        print(f"Products by supermarket: {dict((k, len(v)) for k, v in by_supermarket.items())}")

        # Compare products across different supermarkets
        supermarket_pairs = list(itertools.combinations(by_supermarket.keys(), 2))

        for supermarket1, supermarket2 in supermarket_pairs:
            print(f"Comparing {supermarket1} vs {supermarket2}")

            products1 = by_supermarket[supermarket1]
            products2 = by_supermarket[supermarket2]

            for product1 in products1:
                best_match = None
                best_score = 0.0

                for product2 in products2:
                    score = self.calculate_similarity(product1, product2)

                    if score > best_score and score >= self.similarity_threshold:
                        best_score = score
                        best_match = product2

                if best_match:
                    match = {
                        'match_id': len(matches) + 1,
                        'similarity_score': best_score,
                        'products': [product1, best_match],
                        'product_1': {
                            'supermarket': product1['supermarket'],
                            'name': product1['name'],
                            'price': product1.get('price'),
                            'barcode': product1.get('barcode'),
                            'url': product1.get('url')
                        },
                        'product_2': {
                            'supermarket': best_match['supermarket'],
                            'name': best_match['name'],
                            'price': best_match.get('price'),
                            'barcode': best_match.get('barcode'),
                            'url': best_match.get('url')
                        },
                        'price_difference': None,
                        'cheaper_store': None
                    }

                    # Calculate price difference
                    price1 = product1.get('price')
                    price2 = best_match.get('price')

                    if price1 is not None and price2 is not None:
                        match['price_difference'] = abs(price1 - price2)
                        match['cheaper_store'] = product1['supermarket'] if price1 < price2 else best_match['supermarket']
                        match['price_difference_percentage'] = (abs(price1 - price2) / max(price1, price2)) * 100

                    matches.append(match)

        print(f"Found {len(matches)} potential matches")
        return matches

    def save_matches(self, matches: List[Dict], filename: str):
        """Save matches to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(matches, f, ensure_ascii=False, indent=2, default=str)

        print(f"Matches saved to {filename}")

    def create_comparison_report(self, matches: List[Dict], filename: str):
        """Create a CSV report of price comparisons"""
        if not matches:
            print("No matches to create report")
            return

        report_data = []

        for match in matches:
            if match['product_1']['price'] is not None and match['product_2']['price'] is not None:
                row = {
                    'Product_Name_1': match['product_1']['name'],
                    'Store_1': match['product_1']['supermarket'],
                    'Price_1': match['product_1']['price'],
                    'Product_Name_2': match['product_2']['name'],
                    'Store_2': match['product_2']['supermarket'],
                    'Price_2': match['product_2']['price'],
                    'Price_Difference': match.get('price_difference', 0),
                    'Price_Difference_Percentage': match.get('price_difference_percentage', 0),
                    'Cheaper_Store': match.get('cheaper_store', ''),
                    'Similarity_Score': match['similarity_score'],
                    'Barcode_1': match['product_1'].get('barcode', ''),
                    'Barcode_2': match['product_2'].get('barcode', '')
                }
                report_data.append(row)

        if report_data:
            df = pd.DataFrame(report_data)
            df = df.sort_values('Price_Difference_Percentage', ascending=False)
            df.to_csv(filename, index=False, encoding='utf-8')
            print(f"Price comparison report saved to {filename}")

            # Print summary statistics
            print(f"\n📈 PRICE COMPARISON SUMMARY")
            print("-" * 40)
            print(f"Products with price differences: {len(df)}")
            if len(df) > 0:
                print(f"Average price difference: ${df['Price_Difference'].mean():.2f}")
                print(f"Max price difference: ${df['Price_Difference'].max():.2f}")
                print(f"Average percentage difference: {df['Price_Difference_Percentage'].mean():.1f}%")

                # Store comparison
                cheaper_counts = df['Cheaper_Store'].value_counts()
                print(f"\nCheaper store frequency:")
                for store, count in cheaper_counts.items():
                    print(f"  {store}: {count} products ({count/len(df)*100:.1f}%)")
        else:
            print("No price data available for comparison report")