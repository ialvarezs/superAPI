"""
Database setup and management for storing scraped product data
"""
import sqlite3
import json
from typing import List, Dict, Optional
from datetime import datetime
import pandas as pd


class ProductDatabase:
    def __init__(self, db_path: str = "data/products.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Products table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    supermarket TEXT NOT NULL,
                    name TEXT NOT NULL,
                    price REAL,
                    original_price TEXT,
                    brand TEXT,
                    barcode TEXT,
                    category TEXT DEFAULT 'lacteos',
                    image_url TEXT,
                    product_url TEXT,
                    description TEXT,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(supermarket, name, barcode)
                )
            """)

            # Product matches table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS product_matches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_1_id INTEGER,
                    product_2_id INTEGER,
                    similarity_score REAL,
                    price_difference REAL,
                    cheaper_store TEXT,
                    match_type TEXT DEFAULT 'automatic',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_1_id) REFERENCES products (id),
                    FOREIGN KEY (product_2_id) REFERENCES products (id),
                    UNIQUE(product_1_id, product_2_id)
                )
            """)

            # Scraping sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scraping_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    supermarket TEXT NOT NULL,
                    products_count INTEGER DEFAULT 0,
                    success BOOLEAN DEFAULT TRUE,
                    error_message TEXT,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()

    def save_products(self, products: List[Dict], supermarket: str) -> int:
        """Save products to database"""
        if not products:
            return 0

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Start scraping session
            cursor.execute("""
                INSERT INTO scraping_sessions (supermarket, started_at)
                VALUES (?, ?)
            """, (supermarket, datetime.now()))

            session_id = cursor.lastrowid

            inserted_count = 0

            for product in products:
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO products
                        (supermarket, name, price, original_price, brand, barcode,
                         image_url, product_url, description)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        product.get('supermarket', supermarket),
                        product.get('name'),
                        product.get('price'),
                        product.get('original_price'),
                        product.get('brand'),
                        product.get('barcode'),
                        product.get('image_url'),
                        product.get('url'),
                        product.get('description')
                    ))
                    inserted_count += 1

                except sqlite3.Error as e:
                    print(f"Error inserting product {product.get('name', 'Unknown')}: {e}")

            # Update session
            cursor.execute("""
                UPDATE scraping_sessions
                SET products_count = ?, completed_at = ?
                WHERE id = ?
            """, (inserted_count, datetime.now(), session_id))

            conn.commit()

        print(f"Saved {inserted_count} products to database for {supermarket}")
        return inserted_count

    def save_matches(self, matches: List[Dict]) -> int:
        """Save product matches to database"""
        if not matches:
            return 0

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            inserted_count = 0

            for match in matches:
                try:
                    # Find product IDs
                    product1 = match['product_1']
                    product2 = match['product_2']

                    # Get product 1 ID
                    cursor.execute("""
                        SELECT id FROM products
                        WHERE supermarket = ? AND name = ?
                        LIMIT 1
                    """, (product1['supermarket'], product1['name']))

                    result1 = cursor.fetchone()
                    if not result1:
                        continue

                    # Get product 2 ID
                    cursor.execute("""
                        SELECT id FROM products
                        WHERE supermarket = ? AND name = ?
                        LIMIT 1
                    """, (product2['supermarket'], product2['name']))

                    result2 = cursor.fetchone()
                    if not result2:
                        continue

                    # Insert match
                    cursor.execute("""
                        INSERT OR REPLACE INTO product_matches
                        (product_1_id, product_2_id, similarity_score,
                         price_difference, cheaper_store)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        result1[0],
                        result2[0],
                        match['similarity_score'],
                        match.get('price_difference'),
                        match.get('cheaper_store')
                    ))

                    inserted_count += 1

                except sqlite3.Error as e:
                    print(f"Error inserting match: {e}")

            conn.commit()

        print(f"Saved {inserted_count} matches to database")
        return inserted_count

    def get_products(self, supermarket: Optional[str] = None) -> List[Dict]:
        """Get products from database"""
        with sqlite3.connect(self.db_path) as conn:
            if supermarket:
                query = "SELECT * FROM products WHERE supermarket = ?"
                df = pd.read_sql_query(query, conn, params=(supermarket,))
            else:
                query = "SELECT * FROM products"
                df = pd.read_sql_query(query, conn)

        return df.to_dict('records')

    def get_matches(self) -> List[Dict]:
        """Get product matches with product details"""
        with sqlite3.connect(self.db_path) as conn:
            query = """
                SELECT
                    pm.*,
                    p1.supermarket as supermarket_1,
                    p1.name as name_1,
                    p1.price as price_1,
                    p1.barcode as barcode_1,
                    p2.supermarket as supermarket_2,
                    p2.name as name_2,
                    p2.price as price_2,
                    p2.barcode as barcode_2
                FROM product_matches pm
                JOIN products p1 ON pm.product_1_id = p1.id
                JOIN products p2 ON pm.product_2_id = p2.id
                ORDER BY pm.similarity_score DESC
            """
            df = pd.read_sql_query(query, conn)

        return df.to_dict('records')

    def get_statistics(self) -> Dict:
        """Get database statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Count products by supermarket
            cursor.execute("""
                SELECT supermarket, COUNT(*) as count
                FROM products
                GROUP BY supermarket
            """)
            products_by_store = dict(cursor.fetchall())

            # Total products
            cursor.execute("SELECT COUNT(*) FROM products")
            total_products = cursor.fetchone()[0]

            # Total matches
            cursor.execute("SELECT COUNT(*) FROM product_matches")
            total_matches = cursor.fetchone()[0]

            # Average price by supermarket
            cursor.execute("""
                SELECT supermarket, AVG(price) as avg_price
                FROM products
                WHERE price IS NOT NULL
                GROUP BY supermarket
            """)
            avg_prices = dict(cursor.fetchall())

            # Products with barcodes
            cursor.execute("""
                SELECT COUNT(*) FROM products
                WHERE barcode IS NOT NULL AND barcode != ''
            """)
            products_with_barcodes = cursor.fetchone()[0]

        return {
            'total_products': total_products,
            'products_by_store': products_by_store,
            'total_matches': total_matches,
            'average_prices': avg_prices,
            'products_with_barcodes': products_with_barcodes
        }

    def export_to_csv(self, output_dir: str = "results"):
        """Export all data to CSV files"""
        import os
        os.makedirs(output_dir, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            # Export products
            products_df = pd.read_sql_query("SELECT * FROM products", conn)
            products_df.to_csv(f"{output_dir}/all_products.csv", index=False)

            # Export matches
            matches_query = """
                SELECT
                    pm.similarity_score,
                    pm.price_difference,
                    pm.cheaper_store,
                    p1.supermarket as supermarket_1,
                    p1.name as name_1,
                    p1.price as price_1,
                    p1.barcode as barcode_1,
                    p2.supermarket as supermarket_2,
                    p2.name as name_2,
                    p2.price as price_2,
                    p2.barcode as barcode_2
                FROM product_matches pm
                JOIN products p1 ON pm.product_1_id = p1.id
                JOIN products p2 ON pm.product_2_id = p2.id
            """
            matches_df = pd.read_sql_query(matches_query, conn)
            matches_df.to_csv(f"{output_dir}/product_matches.csv", index=False)

        print(f"Data exported to {output_dir}/ directory")

    def close(self):
        """Close database connection (if needed for connection pooling)"""
        pass