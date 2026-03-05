# 🎯 Targeted Comparison Guide

## Strategy Overview

**Goal:** Get 200 products from Tienda Inglesa as the base, then find matches in Disco and Devoto for price comparison.

**Why this approach?**
- ✅ Tienda Inglesa has the largest e-commerce catalog
- ✅ Better product coverage (200 vs 50-100)
- ✅ More meaningful comparisons (base = most products)
- ✅ Easier to see where you can save money

---

## 🚀 Quick Start

### Run the targeted comparison:

```bash
python targeted_comparison.py
```

**What it does:**
1. Scrapes 200 dairy products from Tienda Inglesa (5-7 min)
2. Searches for those products in Disco (3-5 min)
3. Searches for those products in Devoto (3-5 min)
4. Matches products across stores
5. Creates comparison report

**Total time:** 15-20 minutes

---

## 📊 Expected Results

### Products Scraped:
- **Tienda Inglesa:** 180-200 products (base)
- **Disco:** 40-80 products (matches from Tienda)
- **Devoto:** 40-80 products (matches from Tienda)
- **Total:** 260-360 products

### Matches Expected:
- **Direct matches:** 30-60 products (same product, different stores)
- **Price comparisons:** 25-50 comparisons
- **Savings opportunities:** 10-20 significant deals (>5% difference)

---

## 📁 Output Files

After running, check these files:

### Main Comparison Report
```
results/tienda_base_comparison.csv
```
**Contains:** Product-by-product price comparison with Tienda Inglesa as base

**Columns:**
- Product_Name
- Tienda_Inglesa_Price
- Disco_Price / Devoto_Price
- Price_Difference
- Percentage_Diff
- Cheaper_At (which store is cheaper)
- Savings (how much you save)

**Example:**
```csv
Product_Name,Tienda_Inglesa_Price,Disco_Price,Savings,Cheaper_At
Leche Conaprole 1L,$85,$95,$10,Tienda Inglesa
Yogur Conaprole 1kg,$120,$110,$10,Disco
```

### All Products Data
```
data/tienda_base_all_products.json
```
**Contains:** Complete product data from all 3 stores

### Matches
```
results/tienda_base_matches.json
```
**Contains:** Detailed match information with similarity scores

### Database
```
data/tienda_base_comparison.db
```
**Contains:** SQLite database for SQL queries

---

## 💰 How to Find Best Deals

### Option 1: Open CSV in Excel/Google Sheets
```bash
open results/tienda_base_comparison.csv
```

Then sort by "Savings" column (descending) to see biggest price differences.

### Option 2: Command line
```bash
# Top 10 best deals
head -11 results/tienda_base_comparison.csv | column -t -s','
```

### Option 3: Python analysis
```python
import pandas as pd

df = pd.read_csv('results/tienda_base_comparison.csv')

# Sort by savings
df_sorted = df.sort_values('Savings', ascending=False)

# Products cheaper at Tienda Inglesa
tienda_cheaper = df[df['Cheaper_At'] == 'Tienda Inglesa']

# Products with >10% difference
big_differences = df[df['Percentage_Diff'].str.rstrip('%').astype(float) > 10]

print(f"Products cheaper at Tienda: {len(tienda_cheaper)}")
print(f"Big differences (>10%): {len(big_differences)}")
```

---

## 🔧 Configuration

Edit `targeted_comparison.py` to customize:

### Change target number of products:
```python
runner.run_targeted_comparison(target_products=200)  # Change to 100, 300, etc.
```

### Enable headless mode (no browser window):
```python
runner = TargetedComparisonRunner(headless=True)
```

### Focus on specific brands:
Edit the `extract_search_terms()` method to prioritize certain brands.

---

## 📈 Sample Output

```
🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯
TARGETED COMPARISON STRATEGY
Base: Tienda Inglesa → Search in Disco & Devoto
🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯

================================================================================
STEP 1: SCRAPING TIENDA INGLESA (BASE)
================================================================================
Target: 200 dairy products

✅ Tienda Inglesa: 187 products scraped

================================================================================
STEP 2: SEARCHING IN DISCO
================================================================================
Searching for 42 terms from Tienda Inglesa

✅ Disco: 68 products found

================================================================================
STEP 3: SEARCHING IN DEVOTO
================================================================================
Searching for 42 terms from Tienda Inglesa

✅ Devoto: 64 products found

================================================================================
STEP 4: MATCHING PRODUCTS ACROSS STORES
================================================================================
Total products to match: 319

✅ Found 47 product matches
✅ Matches including Tienda Inglesa: 38

================================================================================
STEP 5: CREATING COMPARISON REPORT
================================================================================

✅ Comparison report saved:
   • results/tienda_base_comparison.csv
   • results/tienda_base_comparison.json

💰 TOP 10 BEST DEALS:
--------------------------------------------------------------------------------

1. Leche Conaprole Entera 1L
   Tienda Inglesa: $85
   Disco: $95
   💵 Save $10 (11.8%) at Tienda Inglesa

2. Yogur Conaprole Natural 1kg
   Tienda Inglesa: $140
   Devoto: $155
   💵 Save $15 (10.7%) at Tienda Inglesa

[... more deals ...]

================================================================================
📊 FINAL SUMMARY
================================================================================

⏱️  Total time: 16.3 minutes

📦 Products scraped:
   • Tienda Inglesa: 187
   • Disco:          68
   • Devoto:         64
   • TOTAL:          319

🔗 Matches found:
   • Total matches:           47
   • With Tienda Inglesa:     38
   • Price comparisons ready: 38

📁 Output files:
   • results/tienda_base_comparison.csv
   • results/tienda_base_comparison.json
   • data/tienda_base_all_products.json
   • data/tienda_base_comparison.db

✅ TARGETED COMPARISON COMPLETE!
```

---

## 🎓 Understanding the Results

### Good Match Rate
If you get 30-50 matches from 200 base products, that's **15-25% match rate** - this is normal and expected because:
- Different stores stock different products
- Same products may have different descriptions
- Some products are store-exclusive brands

### Price Patterns Expected
- **Tienda Inglesa** typically competitive on branded items
- **Disco/Devoto** may be cheaper on store brands
- **5-15% differences** are common
- **20%+ differences** indicate promotional pricing

### What Makes a "Good Deal"
- **>5% difference:** Worth considering
- **>10% difference:** Definitely worth switching stores
- **>20% difference:** Likely a promotion or special offer

---

## 🐛 Troubleshooting

### "No matches found"
**Cause:** Product names too different between stores  
**Solution:** The matcher uses fuzzy matching, but some products are genuinely unique to each store

### "Only a few products from Disco/Devoto"
**Cause:** The base scraper doesn't do targeted searching yet  
**Solution:** This is expected with current implementation. The products found are from general category scraping.

### "Takes longer than expected"
**Cause:** Anti-bot delays are working correctly  
**Solution:** This is normal. Don't reduce delays or you'll get blocked.

### "Rate limited / blocked"
**Cause:** Running too frequently or too fast  
**Solution:** Wait 1-2 hours between runs. Run during off-peak hours (3-5 AM Uruguay time).

---

## 🎯 Next Steps After Running

1. **Analyze the CSV report**
   - Sort by savings
   - Identify patterns (which store is cheaper for what?)
   - Look for brand-specific trends

2. **Build a shopping list optimizer**
   - Use the comparison data
   - Calculate total savings for a basket of products
   - Recommend which store to use for each item

3. **Track prices over time**
   - Run weekly
   - Store historical data
   - Identify price trends and promotions

4. **Create a web dashboard**
   - Visualize price differences
   - Show best deals
   - Allow product search

---

## 💡 Pro Tips

1. **Run during off-peak hours** (3-5 AM Uruguay time) for best results
2. **Check results after 5-10 minutes** - you can review partial data while scraping continues
3. **Focus on frequently-bought items** - customize search terms for your needs
4. **Run weekly** - prices change, promotions come and go
5. **Combine with delivery costs** - sometimes the "cheaper" store costs more after delivery

---

## 📞 Quick Reference

**Start comparison:**
```bash
python targeted_comparison.py
```

**View results:**
```bash
# CSV (best for humans)
open results/tienda_base_comparison.csv

# JSON (best for code)
cat results/tienda_base_comparison.json | jq '.[0:5]'

# Database (best for SQL queries)
sqlite3 data/tienda_base_comparison.db "SELECT * FROM products LIMIT 10"
```

**Re-run with different settings:**
```bash
# Edit the file first
nano targeted_comparison.py

# Then run again
python targeted_comparison.py
```

---

✅ **Ready to find the best grocery deals in Uruguay!** 🛒��🇾

