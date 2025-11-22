import folium
import json
import pandas as pd
import os

# Lire le CSV STEP03
df = pd.read_csv("csv\STEP03_maisons_dept29.csv")

# Créer un dict GPS -> nom de commune
commune_names = {}
for index, row in df.iterrows():
    if pd.notna(row['GPS']) and row['GPS'] != '':
        lieu = row['Lieu']
        if pd.notna(lieu):
            parts = lieu.strip().rsplit(None, 1)
            if len(parts) == 2 and parts[1].isdigit() and len(parts[1]) == 5:
                ville = parts[0].strip().replace('-', ' ').upper()
                commune_names[row['GPS']] = ville

# Filtrer les lignes avec GPS non vide et récupérer les valeurs uniques
unique_gps = df[df['GPS'].notna() & (df['GPS'] != '')]['GPS'].unique()

# Créer une carte centrée sur Paris
m = folium.Map(location=[48.8566, 2.3522], zoom_start=10, tiles='CartoDB dark_matter')

# Ajouter chaque GeoJSON unique à la carte
for gps in unique_gps:
    try:
        geojson_data = json.loads(gps)
        name = commune_names.get(gps, "Inconnu")
        folium.GeoJson(
            geojson_data, 
            name="Contour de la commune",
            tooltip=name,
            style_function=lambda x: {'fillColor': 'lightblue', 'color': 'blue', 'weight': 2, 'fillOpacity': 0.3}
        ).add_to(m)
    except json.JSONDecodeError:
        print(f"Erreur de parsing JSON pour : {gps[:50]}...")

# Ajouter un contrôle des couches
folium.LayerControl().add_to(m)

# Sauvegarder la carte dans un fichier HTML
os.makedirs("map", exist_ok=True)
m.save("map/map.html")