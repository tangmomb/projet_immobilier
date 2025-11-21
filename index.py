import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random

# List of User-Agents to rotate
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
]

# Function to get random headers
def get_random_headers():
    return {
        "User-Agent": random.choice(user_agents),
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Referer": "https://www.google.com/",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

# Base URL
base_url = "https://www.etreproprio.com/annonces/th.ld75"

# Use a session to persist cookies
session = requests.Session()

# Find property listings across pages
total_properties = 0
page = 1
first_page = True
while True:
    url = f"{base_url}.odd.g{page}#list"
    print(f"Scraping page {page}: {url}")
    
    try:
        # Send GET request with random headers
        headers = get_random_headers()
        response = session.get(url, headers=headers)
        
        # Check for 404 or other client errors
        if response.status_code == 404:
            print(f"Page {page} not found (404). Stopping.")
            break
        response.raise_for_status()  # Check for other errors
        
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
        
        # Create DataFrame for this page and append to CSV
        df = pd.DataFrame(page_properties)
        df.to_csv('properties.csv', mode='a' if not first_page else 'w', header=first_page, index=False)
        first_page = False
        
        total_properties += len(page_properties)
        print(f"Found and saved {len(page_properties)} properties on page {page}.")
        
    except requests.exceptions.RequestException as e:
        print(f"Error on page {page}: {e}. Stopping.")
        break
    
    page += 1
    
    # Random wait between 5-15 seconds to avoid overloading
    wait_time = random.uniform(5, 15)
    print(f"Waiting {wait_time:.2f} seconds...")
    time.sleep(wait_time)

print(f"Total properties scraped and saved: {total_properties}")