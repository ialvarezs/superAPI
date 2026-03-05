"""Debug script to check what's happening with the response"""
import requests
from bs4 import BeautifulSoup
import re
import time
import random

# Rotating user agents
user_agents = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
]

url = "https://www.tiendainglesa.com.uy/supermercado/categoria/almacen/arroz-legumbres/78/84"

session = requests.Session()
session.headers.update({
    'User-Agent': random.choice(user_agents),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'es-UY,es;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Cache-Control': 'max-age=0',
    'DNT': '1'
})

print("Fetching page...")
time.sleep(2)

response = session.get(url, timeout=30)
print(f"Status: {response.status_code}")
print(f"Response length: {len(response.text)}")
print(f"\nFirst 500 chars:\n{response.text[:500]}")

soup = BeautifulSoup(response.text, 'html.parser')
links = soup.find_all('a', href=re.compile(r'\.producto\?', re.I))
print(f"\n\nFound {len(links)} product links")

# Check for arroz
arroz_urls = []
for link in links:
    href = link.get('href')
    url_full = href if href.startswith('http') else 'https://www.tiendainglesa.com.uy' + href
    link_text = link.get_text().lower()
    
    if 'arroz' in link_text or 'arroz' in url_full.lower():
        if url_full not in arroz_urls:
            arroz_urls.append(url_full)

print(f"Found {len(arroz_urls)} arroz URLs")
for i, u in enumerate(arroz_urls[:5], 1):
    print(f"{i}. {u}")
