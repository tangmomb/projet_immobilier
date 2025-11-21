import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import sys
import os

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

# Function to scrape properties
def scrape_properties(base_url, csv_filename):
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
            df.to_csv(csv_filename, mode='a' if not first_page else 'w', header=first_page, index=False)
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

# Function to get detailed info from property URLs
def get_property_details(csv_filename):
    # Read the CSV
    df = pd.read_csv(csv_filename)
    
    # Add new columns
    df['Prix'] = None
    df['Lieu'] = None
    df['Taille'] = None
    df['Taille_terrain'] = None
    df['Pieces'] = None
    
    # Save to new CSV STEP02
    new_csv_filename = csv_filename.replace('STEP01', 'STEP02')
    
    # Use a session
    session = requests.Session()
    
    for index, row in df.iterrows():
        url = row['Lien']
        print(f"Fetching details for: {url}")
        
        try:
            headers = get_random_headers()
            response = session.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Price
            price_div = soup.select_one('.ep-price')
            if price_div:
                price = price_div.get_text(strip=True).replace('€', '').replace('\xa0', '').strip()
                df.at[index, 'Prix'] = price
            
            # Area
            area_div = soup.select_one('.ep-area')
            if area_div:
                # Main area
                main_area_text = area_div.get_text().strip()
                if ' / ' in main_area_text:
                    main_area = main_area_text.split(' / ')[0].replace('m²', '').strip()
                else:
                    main_area = main_area_text.replace('m²', '').strip()
                df.at[index, 'Taille'] = main_area
                
                # Land area from span
                land_span = area_div.select_one('.dtl-main-surface-terrain')
                if land_span:
                    land_text = land_span.get_text().strip().replace('/', '').replace('m²', '').strip()
                    df.at[index, 'Taille_terrain'] = land_text
            
            # Rooms
            room_div = soup.select_one('.ep-room')
            if room_div:
                rooms = room_div.get_text(strip=True).replace('pièces', '').replace('pièce', '').strip()
                df.at[index, 'Pieces'] = rooms
            
            # Location
            loc_div = soup.select_one('.ep-loc')
            if loc_div:
                loc = loc_div.get_text(strip=True).replace('—', '').strip()
                df.at[index, 'Lieu'] = loc
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
        
        # Save incrementally
        df.to_csv(new_csv_filename, index=False)
        
        # Wait between requests
        wait_time = random.uniform(5, 15)
        print(f"Waiting {wait_time:.2f} seconds...")
        time.sleep(wait_time)
    
    print(f"Details saved in {new_csv_filename}")

# Create csv directory if it doesn't exist
os.makedirs('csv', exist_ok=True)

# Ask user for step
step = input("Étape : 1 (scraping initial) ou 2 (détails) ? ").strip()
if step not in ['1', '2']:
    print("Étape invalide. Arrêt du script.")
    sys.exit(1)

# Ask user for city choice
city = input("Ville et 50 km autour : Paris (p), Lyon (l), Marseille (m) ou Bordeaux (b) ? ").strip().lower()
postal_codes = {'p': '75056', 'l': '69123', 'm': '13055', 'b': '33063'}
city_names = {'p': 'paris', 'l': 'lyon', 'm': 'marseille', 'b': 'bordeaux'}
if city in postal_codes:
    city_name = city_names[city]
    code = postal_codes[city]
    base_houses = f"https://www.etreproprio.com/annonces/th.lc{code}-r50"
    base_aparts = f"https://www.etreproprio.com/annonces/tf.lc{code}-r50"
else:
    print("Ville invalide. Arrêt du script.")
    sys.exit(1)

# Ask user for property type
choice = input("Type : maisons (h) ou appartements (a) ? ").strip().lower()
if choice == 'h':
    base_url = base_houses
    csv_filename = f'csv/STEP01_maisons_{city_name}.csv'
    print(f"Scraping des maisons à {city_name}.")
elif choice == 'a':
    base_url = base_aparts
    csv_filename = f'csv/STEP01_appartements_{city_name}.csv'
    print(f"Scraping des appartements à {city_name}.")
else:
    print("Type invalide. Arrêt du script.")
    sys.exit(1)

# Execute based on step
if step == '1':
    scrape_properties(base_url, csv_filename)
elif step == '2':
    if not os.path.exists(csv_filename):
        print(f"Le fichier {csv_filename} n'existe pas. Veuillez d'abord exécuter l'étape 1.")
        sys.exit(1)
    get_property_details(csv_filename)

