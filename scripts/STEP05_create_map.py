import folium
import json
import pandas as pd
import os

# Lire le CSV all_bretagne_with_gps
csv_file = 'csv/all_bretagne_with_gps.csv'
if not os.path.exists(csv_file):
    print(f"Le fichier {csv_file} n'existe pas.")
    exit(1)

df = pd.read_csv(csv_file)

# Filtrer les lignes avec GPS non vide
df = df[df['GPS'].notna() & (df['GPS'] != '')]

# Calculer les valeurs min et max pour la normalisation des couleurs
valid_avgs = df['Prix moyen au m2'].dropna()
if not valid_avgs.empty:
    min_price = valid_avgs.min()
    max_price = valid_avgs.max()
else:
    min_price = 0
    max_price = 1  # dummy

# Créer une carte centrée sur la Bretagne
m = folium.Map(location=[48.1, -3.15], zoom_start=8, tiles='CartoDB positron')

# Ajouter chaque GeoJSON à la carte
for index, row in df.iterrows():
    try:
        geojson_data = json.loads(row['GPS'])
        lieu = row['Lieu']
        if pd.notna(lieu):
            parts = lieu.strip().rsplit(None, 1)
            if len(parts) == 2:
                name = parts[0].strip()
            else:
                name = lieu.strip()
        else:
            name = "Inconnu"
        count = row['Nombre de maisons à vendre']
        avg_price = row['Prix moyen au m2']
        
        # Calculer la couleur basée sur le prix moyen
        if pd.notna(avg_price) and max_price > min_price:
            norm = (avg_price - min_price) / (max_price - min_price)
            r = int(255 * norm)
            g = int(255 * (1 - norm))
            b = 0
            fill_color = f'#{r:02x}{g:02x}{b:02x}'
        else:
            fill_color = 'gray'
        
        folium.GeoJson(
            geojson_data, 
            name="Contour de la commune",
            tooltip=f"{name}<br>Maisons à vendre: {count}<br>Prix moyen/m²: {avg_price if pd.notna(avg_price) else 'N/A'} €",
            style_function=lambda x, color=fill_color: {'fillColor': color, 'color': 'grey', 'weight': 2, 'fillOpacity': 0.3}
        ).add_to(m)
    except json.JSONDecodeError:
        print(f"Erreur de parsing JSON pour : {row['GPS'][:50]}...")


# Sauvegarder la carte dans un fichier HTML
os.makedirs("map", exist_ok=True)
m.save("map/map.html")