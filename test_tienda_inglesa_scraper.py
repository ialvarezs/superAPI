"""
Quick test script to validate Tienda Inglesa scraping approach
Tests both category and search strategies
"""
import sys
from tienda_inglesa_production_scraper import TiendaInglesaScraper


def test_search_strategy():
    """Test search-based scraping (fastest validation)"""
    print("\n" + "="*70)
    print("TEST 1: SEARCH STRATEGY")
    print("="*70)
    print("Testing search-based product discovery...")
    print("Expected: 10-20 products from 'leche' search\n")
    
    scraper = TiendaInglesaScraper(headless=False, max_products=20)
    
    try:
        products = scraper.scrape_with_strategy(strategy='search')
        
        # Validate results
        assert len(products) > 0, "No products found!"
        assert all(p.get('name') for p in products), "Some products missing names"
        
        products_with_prices = sum(1 for p in products if p.get('price'))
        price_coverage = (products_with_prices / len(products)) * 100
        
        print(f"\n✅ TEST PASSED")
        print(f"   Products found: {len(products)}")
        print(f"   Price coverage: {price_coverage:.1f}%")
        
        return True, products
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False, []
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False, []


def test_category_strategy():
    """Test category-based scraping"""
    print("\n" + "="*70)
    print("TEST 2: CATEGORY STRATEGY")
    print("="*70)
    print("Testing category-based product discovery...")
    print("Expected: Products from lacteos categories\n")
    
    scraper = TiendaInglesaScraper(headless=False, max_products=30)
    
    try:
        products = scraper.scrape_with_strategy(strategy='category')
        
        # Validate results
        assert len(products) > 0, "No products found!"
        
        products_with_brands = sum(1 for p in products if p.get('brand'))
        brand_coverage = (products_with_brands / len(products)) * 100
        
        print(f"\n✅ TEST PASSED")
        print(f"   Products found: {len(products)}")
        print(f"   Brand coverage: {brand_coverage:.1f}%")
        
        return True, products
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False, []
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        return False, []


def test_hybrid_strategy():
    """Test hybrid strategy (recommended)"""
    print("\n" + "="*70)
    print("TEST 3: HYBRID STRATEGY (RECOMMENDED)")
    print("="*70)
    print("Testing combined category + search approach...")
    print("Expected: Maximum product coverage\n")
    
    scraper = TiendaInglesaScraper(headless=False, max_products=50)
    
    try:
        products = scraper.scrape_with_strategy(strategy='hybrid')
        
        # Validate results
        assert len(products) > 0, "No products found!"
        
        # Quality checks
        products_with_prices = sum(1 for p in products if p.get('price'))
        products_with_brands = sum(1 for p in products if p.get('brand'))
        products_with_images = sum(1 for p in products if p.get('image_url'))
        products_with_urls = sum(1 for p in products if p.get('url'))
        
        print(f"\n✅ TEST PASSED")
        print(f"\n📊 Results Summary:")
        print(f"   Total products: {len(products)}")
        print(f"   With prices: {products_with_prices} ({products_with_prices/len(products)*100:.1f}%)")
        print(f"   With brands: {products_with_brands} ({products_with_brands/len(products)*100:.1f}%)")
        print(f"   With images: {products_with_images} ({products_with_images/len(products)*100:.1f}%)")
        print(f"   With URLs: {products_with_urls} ({products_with_urls/len(products)*100:.1f}%)")
        
        # Show sample products
        print(f"\n🥛 Sample Products:")
        for i, p in enumerate(products[:5], 1):
            print(f"   {i}. {p['name'][:60]}")
            print(f"      ${p.get('price', 'N/A')} | {p.get('brand', 'Unknown brand')}")
        
        # Save test results
        scraper.save_results('test_hybrid_results')
        
        return True, products
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False, []
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False, []


def run_all_tests():
    """Run all validation tests"""
    print("\n" + "🧪"*35)
    print("TIENDA INGLESA SCRAPER VALIDATION SUITE")
    print("🧪"*35)
    
    results = {
        'search': False,
        'category': False,
        'hybrid': False
    }
    
    # Test 1: Search strategy (fastest)
    success, products = test_search_strategy()
    results['search'] = success
    
    if not success:
        print("\n⚠️  Search strategy failed. Skipping remaining tests.")
        print("    This likely means:")
        print("    - Network connectivity issues")
        print("    - Site structure has changed")
        print("    - Anti-bot protection triggered")
        return results
    
    # Test 2: Category strategy
    # success, products = test_category_strategy()
    # results['category'] = success
    
    # Test 3: Hybrid strategy (recommended for production)
    success, products = test_hybrid_strategy()
    results['hybrid'] = success
    
    # Final summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    
    for strategy, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"   {strategy.upper():12s}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("   The scraper is working correctly and ready for production.")
        print("\n📂 Next steps:")
        print("   1. Review results in data/test_hybrid_results.json")
        print("   2. Run production_scraper_runner.py for full scraping")
        print("   3. Check TIENDA_INGLESA_SCRAPING_GUIDE.md for best practices")
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("   Please review error messages above and:")
        print("   1. Check internet connectivity")
        print("   2. Verify Chrome/ChromeDriver is installed")
        print("   3. Review TIENDA_INGLESA_SCRAPING_GUIDE.md for troubleshooting")
    
    return results


if __name__ == "__main__":
    print("\n🚀 Starting Tienda Inglesa Scraper Tests...")
    print("⏱️  This will take 3-5 minutes to complete.\n")
    
    try:
        results = run_all_tests()
        
        # Exit code based on results
        if all(results.values()):
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Failure
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(2)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(3)
