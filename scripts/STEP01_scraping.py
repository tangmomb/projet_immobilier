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
async def scrape_properties(base_url, com, csv_filename, lock_write, existing_links, lock_links):
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
                                        page_properties.append({'Ville': city, 'Nom': name, 'Lien': full_link, 'Code INSEE': com, 'Page Lien': url})
                    
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

# Create csv directory if it doesn't exist
os.makedirs('csv', exist_ok=True)
os.makedirs('csv/STEP01', exist_ok=True)

# Ask user for department number
dept = input("Numéro du département : ").strip()
if not dept.isdigit() or len(dept) < 1 or len(dept) > 3:
    print("Numéro de département invalide. Arrêt du script.")
    sys.exit(1)

# Ask user for property type
choice = input("Type : maisons (h) ou appartements (a) ? ").strip().lower()
if choice == 'h':
    prefix = 'th'
    csv_filename = f'csv/STEP01/STEP01_maisons_dept{dept}.csv'
    print(f"Scraping des maisons dans le département {dept}.")
elif choice == 'a':
    prefix = 'tf'
    csv_filename = f'csv/STEP01/STEP01_appartements_dept{dept}.csv'
    print(f"Scraping des appartements dans le département {dept}.")
else:
    print("Type invalide. Arrêt du script.")
    sys.exit(1)

# Load communes from the department-specific CSV
communes_csv = f'csv/STEP00/communes_dept{dept}.csv'
if os.path.exists(communes_csv):
    df_communes = pd.read_csv(communes_csv)
    coms = df_communes['COM'].tolist()
    print(f"Chargé {len(coms)} communes depuis {communes_csv}.")
else:
    print(f"Le fichier {communes_csv} n'existe pas. Veuillez le créer d'abord en utilisant le notebook explore_csv.ipynb.")
    sys.exit(1)

# Create CSV with headers if it doesn't exist
pd.DataFrame(columns=['Ville', 'Nom', 'Lien', 'Code INSEE', 'Page Lien']).to_csv(csv_filename, index=False)

# Load existing links to avoid duplicates
existing_links = set()

lock_write = asyncio.Lock()
lock_links = asyncio.Lock()

async def scrape_city(com):
    base_url = f"https://www.etreproprio.com/annonces/{prefix}.lc{com}-r0"
    print(f"Scraping pour la commune {com}...")
    await scrape_properties(base_url, com, csv_filename, lock_write, existing_links, lock_links)

semaphore = asyncio.Semaphore(3)  # Limit concurrent cities to 3

async def main():
    tasks = []
    for com in coms:
        async def limited_scrape(com=com):
            async with semaphore:
                await scrape_city(com)
        tasks.append(limited_scrape())
    await asyncio.gather(*tasks)

asyncio.run(main())