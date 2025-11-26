from bs4 import BeautifulSoup
import pandas as pd
import random
import sys
import os
import asyncio
import aiohttp

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
async def scrape_properties(base_url, csv_filename, lock_write, existing_links, lock_links):
    async with aiohttp.ClientSession() as session:
        total_properties = 0
        page = 1
        while True:
            url = f"{base_url}.odd.g{page}#list"
            print(f"Scraping page {page}: {url}")
            
            try:
                headers = get_random_headers()
                async with session.get(url, headers=headers) as response:
                    if response.status == 404:
                        print(f"Page {page} not found (404). Stopping.")
                        break
                    response.raise_for_status()
                    
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    page_properties = []
                    for card in soup.select('.card-cla-search'):
                        a = card.find_parent('a')
                        if a and 'href' in a.attrs:
                            href = a['href']
                            title_div = card.select_one('.ep-title')
                            if title_div:
                                name = title_div.get_text(strip=True)
                                city_div = card.select_one('.ep-city')
                                city = city_div.get_text(strip=True) if city_div else ''
                                full_link = f"https://www.etreproprio.com{href}" if href.startswith('/') else href
                                async with lock_links:
                                    if full_link not in existing_links:
                                        existing_links.add(full_link)
                                        page_properties.append({'Ville': city, 'Nom': name, 'Lien': full_link})
                    
                    if not page_properties:
                        print(f"No more properties on page {page}. Stopping.")
                        break
                    
                    df = pd.DataFrame(page_properties)
                    async with lock_write:
                        df.to_csv(csv_filename, mode='a', header=False, index=False)
                    
                    total_properties += len(page_properties)
                    print(f"Found and saved {len(page_properties)} properties on page {page}.")
                    
            except aiohttp.ClientError as e:
                print(f"Error on page {page}: {e}. Stopping.")
                break
            
            page += 1
            
            wait_time = random.uniform(5, 15)
            print(f"Waiting {wait_time:.2f} seconds...")
            await asyncio.sleep(wait_time)
    
    print(f"Total properties scraped and saved: {total_properties}")

# Function to get detailed info from property URLs
async def get_property_details(csv_filename):
    # Read the CSV
    df = pd.read_csv(csv_filename)
    
    # Add new columns
    df['Prix'] = None
    df['Lieu'] = None
    df['Taille'] = None
    df['Taille_terrain'] = None
    df['Pieces'] = None
    
    # Remove 'Ville' column as it duplicates with 'Lieu'
    df = df.drop(columns=['Ville'])
    
    # Save to new CSV STEP02
    new_csv_filename = csv_filename.replace('STEP01', 'STEP02')
    
    semaphore = asyncio.Semaphore(5)  # Limit concurrent requests
    
    async def fetch_details(session, index, url):
        async with semaphore:
            try:
                headers = get_random_headers()
                async with session.get(url, headers=headers) as response:
                    response.raise_for_status()
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    details = {}
                    
                    # Price
                    price_div = soup.select_one('.ep-price')
                    if price_div:
                        price = price_div.get_text(strip=True).replace('€', '').replace('\xa0', '').strip()
                        details['Prix'] = price
                    
                    # Area
                    area_div = soup.select_one('.ep-area')
                    if area_div:
                        main_area_text = area_div.get_text().strip()
                        if ' / ' in main_area_text:
                            main_area = main_area_text.split(' / ')[0].replace('m²', '').strip()
                        else:
                            main_area = main_area_text.replace('m²', '').strip()
                        details['Taille'] = main_area
                        
                        land_span = area_div.select_one('.dtl-main-surface-terrain')
                        if land_span:
                            land_text = land_span.get_text().strip().replace('/', '').replace('m²', '').strip()
                            details['Taille_terrain'] = land_text
                    
                    # Rooms
                    room_div = soup.select_one('.ep-room')
                    if room_div:
                        rooms = room_div.get_text(strip=True).replace('pièces', '').replace('pièce', '').strip()
                        details['Pieces'] = rooms
                    
                    # Location
                    loc_div = soup.select_one('.ep-loc')
                    if loc_div:
                        loc = loc_div.get_text(strip=True).replace('—', '').strip()
                        details['Lieu'] = loc
                    
                    # Wait
                    await asyncio.sleep(random.uniform(1, 5))
                    
                    return index, details
                    
            except aiohttp.ClientError as e:
                print(f"Error fetching {url}: {e}")
                return index, {}
    
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_details(session, index, row['Lien']) for index, row in df.iterrows()]
        
        for coro in asyncio.as_completed(tasks):
            index, details = await coro
            if details:
                for key, value in details.items():
                    df.at[index, key] = value
            df.to_csv(new_csv_filename, index=False)
    
    print(f"Details saved in {new_csv_filename}")

# Create csv directory if it doesn't exist
os.makedirs('csv', exist_ok=True)

# Ask user for step
step = input("Étape : 1 (scraping initial) ou 2 (détails) ? ").strip()
if step not in ['1', '2']:
    print("Étape invalide. Arrêt du script.")
    sys.exit(1)

# Ask user for department number
dept = input("Numéro du département : ").strip()
if not dept.isdigit() or len(dept) < 1 or len(dept) > 3:
    print("Numéro de département invalide. Arrêt du script.")
    sys.exit(1)

# Ask user for property type
choice = input("Type : maisons (h) ou appartements (a) ? ").strip().lower()
if choice == 'h':
    prefix = 'th'
    csv_filename = f'csv/STEP01_maisons_dept{dept}.csv'
    print(f"Scraping des maisons dans le département {dept}.")
elif choice == 'a':
    prefix = 'tf'
    csv_filename = f'csv/STEP01_appartements_dept{dept}.csv'
    print(f"Scraping des appartements dans le département {dept}.")
else:
    print("Type invalide. Arrêt du script.")
    sys.exit(1)

# Load code_insee.csv and filter cities in the department
df_insee = pd.read_csv('csv/code_insee.csv')
coms = df_insee[df_insee['COM'].str.startswith(dept)]['COM'].tolist()
if not coms:
    print(f"Aucune commune trouvée pour le département {dept}.")
    sys.exit(1)

print(f"Trouvé {len(coms)} communes dans le département {dept}.")

# Execute based on step
if step == '1':
    # Create CSV with headers if it doesn't exist
    if not os.path.exists(csv_filename):
        pd.DataFrame(columns=['Ville', 'Nom', 'Lien']).to_csv(csv_filename, index=False)
    
    # Load existing links to avoid duplicates
    existing_links = set()
    if os.path.exists(csv_filename):
        df_existing = pd.read_csv(csv_filename)
        existing_links = set(df_existing['Lien'].tolist())
    
    lock_write = asyncio.Lock()
    lock_links = asyncio.Lock()
    
    async def scrape_city(com):
        base_url = f"https://www.etreproprio.com/annonces/{prefix}.lc{com}-r0"
        print(f"Scraping pour la commune {com}...")
        await scrape_properties(base_url, csv_filename, lock_write, existing_links, lock_links)
    
    semaphore = asyncio.Semaphore(5)  # Limit concurrent cities to 5
    
    async def main():
        tasks = []
        for com in coms:
            async def limited_scrape(com=com):
                async with semaphore:
                    await scrape_city(com)
            tasks.append(limited_scrape())
        await asyncio.gather(*tasks)
    
    asyncio.run(main())
    
elif step == '2':
    if not os.path.exists(csv_filename):
        print(f"Le fichier {csv_filename} n'existe pas. Veuillez d'abord exécuter l'étape 1.")
        sys.exit(1)
    asyncio.run(get_property_details(csv_filename))

