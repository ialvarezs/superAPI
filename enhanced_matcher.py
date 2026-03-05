"""
Enhanced product matcher with barcode, name, and brand matching
"""
from typing import List, Dict, Tuple
import re
from difflib import SequenceMatcher
from logger import setup_logger

logger = setup_logger('enhanced_matcher')

class EnhancedProductMatcher:
    """Match products across supermarkets using multiple strategies"""
    
    def __init__(self, similarity_threshold: float = 0.75):
        self.similarity_threshold = similarity_threshold
    
    def match_products(self, products_by_store: Dict[str, List[Dict]]) -> List[Dict]:
        """Match products across all supermarkets"""
        logger.info("Starting product matching across supermarkets")
        
        all_matches = []
        stores = list(products_by_store.keys())
        
        # Compare each pair of stores
        for i in range(len(stores)):
            for j in range(i + 1, len(stores)):
                store1, store2 = stores[i], stores[j]
                products1 = products_by_store[store1]
                products2 = products_by_store[store2]
                
                logger.info(f"Matching {store1} ({len(products1)} products) with {store2} ({len(products2)} products)")
                
                matches = self._match_store_pair(products1, products2, store1, store2)
                all_matches.extend(matches)
                
                logger.info(f"Found {len(matches)} matches between {store1} and {store2}")
        
        logger.info(f"Total matches found: {len(all_matches)}")
        return all_matches
    
    def _match_store_pair(self, products1: List[Dict], products2: List[Dict], 
                          store1: str, store2: str) -> List[Dict]:
        """Match products between two stores"""
        matches = []
        
        for p1 in products1:
            best_match = None
            best_score = 0
            best_match_type = None
            
            for p2 in products2:
                # Try barcode match first (most reliable)
                if self._has_valid_identifier(p1) and self._has_valid_identifier(p2):
                    if self._identifiers_match(p1, p2):
                        score = 1.0
                        match_type = 'barcode'
                        
                        if score > best_score:
                            best_score = score
                            best_match = p2
                            best_match_type = match_type
                        continue
                
                # Name and brand similarity
                name_score = self._calculate_name_similarity(p1, p2)
                
                if name_score >= self.similarity_threshold:
                    if name_score > best_score:
                        best_score = name_score
                        best_match = p2
                        best_match_type = 'name_similarity'
            
            # Record match if found
            if best_match and best_score >= self.similarity_threshold:
                match = self._create_match_record(p1, best_match, best_score, best_match_type)
                matches.append(match)
        
        return matches
    
    def _has_valid_identifier(self, product: Dict) -> bool:
        """Check if product has valid barcode/EAN/GTIN"""
        for field in ['barcode', 'ean', 'gtin']:
            value = product.get(field)
            if value and str(value).strip() and len(str(value)) >= 8:
                return True
        return False
    
    def _identifiers_match(self, p1: Dict, p2: Dict) -> bool:
        """Check if product identifiers match"""
        for field in ['barcode', 'ean', 'gtin']:
            val1 = str(p1.get(field, '')).strip().lstrip('0')
            val2 = str(p2.get(field, '')).strip().lstrip('0')
            
            if val1 and val2 and len(val1) >= 8 and len(val2) >= 8:
                if val1 == val2:
                    return True
        return False
    
    def _calculate_name_similarity(self, p1: Dict, p2: Dict) -> float:
        """Calculate similarity between product names"""
        name1 = self._normalize_name(p1.get('name', ''))
        name2 = self._normalize_name(p2.get('name', ''))
        
        if not name1 or not name2:
            return 0.0
        
        # Base similarity
        base_score = SequenceMatcher(None, name1, name2).ratio()
        
        # Boost for matching brands
        brand1 = self._normalize_name(p1.get('brand', ''))
        brand2 = self._normalize_name(p2.get('brand', ''))
        
        if brand1 and brand2 and brand1 == brand2:
            base_score = min(1.0, base_score * 1.2)
        
        # Boost for matching key terms (arroz type, weight)
        key_terms1 = self._extract_key_terms(name1)
        key_terms2 = self._extract_key_terms(name2)
        
        common_terms = key_terms1.intersection(key_terms2)
        if common_terms:
            boost = len(common_terms) * 0.1
            base_score = min(1.0, base_score + boost)
        
        return base_score
    
    def _normalize_name(self, name: str) -> str:
        """Normalize product name for comparison"""
        if not name:
            return ""
        
        name = name.lower()
        name = re.sub(r'[^\w\s]', ' ', name)
        name = re.sub(r'\s+', ' ', name)
        return name.strip()
    
    def _extract_key_terms(self, name: str) -> set:
        """Extract key terms from product name"""
        key_patterns = [
            r'\d+\s*(?:kg|g|gr|gramos?|kilos?)',  # Weight
            r'\d+\s*(?:un|unidades?|u)',  # Units
            r'(?:blanco|integral|parboil|largo|corto)',  # Rice types
        ]
        
        terms = set()
        for pattern in key_patterns:
            matches = re.findall(pattern, name, re.I)
            terms.update([m.strip() for m in matches])
        
        return terms
    
    def _create_match_record(self, p1: Dict, p2: Dict, score: float, match_type: str) -> Dict:
        """Create match record with price comparison"""
        price1 = p1.get('price')
        price2 = p2.get('price')
        
        price_diff = None
        cheaper_store = None
        
        if price1 and price2:
            price_diff = abs(price1 - price2)
            cheaper_store = p1['supermarket'] if price1 < price2 else p2['supermarket']
        
        return {
            'product_1': p1,
            'product_2': p2,
            'similarity_score': score,
            'match_type': match_type,
            'price_difference': price_diff,
            'cheaper_store': cheaper_store,
            'savings_percentage': (price_diff / max(price1, price2) * 100) if price1 and price2 else None
        }
