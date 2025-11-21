import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# Headers to mimic a real browser
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
    "Referer": "https://www.google.com/",
    "Connection": "keep-alive"
}

# Base URL
base_url = "https://www.etreproprio.com/annonces/th.ld75"

# Find property listings across pages
properties = []
page = 1
while True:
    url = f"{base_url}.odd.g{page}#list"
    print(f"Scraping page {page}: {url}")
    
    # Send GET request with headers
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Check for errors
    
    # Parse HTML
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find property listings on this page
    page_properties = []
    for card in soup.select('.card-cla-search'):
        a = card.find_parent('a')
        if a and 'href' in a.attrs:
            href = a['href']
            title_div = card.select_one('.ep-title')
            if title_div:
                name = title_div.get_text(strip=True)
                full_link = f"https://www.etreproprio.com{href}" if href.startswith('/') else href
                page_properties.append({'Nom': name, 'Lien': full_link})
    
    # If no properties on this page, stop
    if not page_properties:
        print(f"No more properties on page {page}. Stopping.")
        break
    
    properties.extend(page_properties)
    print(f"Found {len(page_properties)} properties on page {page}.")
    
    page += 1
    
    # Wait to avoid overloading the site
    time.sleep(2)

# Create DataFrame
df = pd.DataFrame(properties)

# Save to CSV
df.to_csv('properties.csv', index=False)
print(f"Total properties scraped: {len(properties)}")