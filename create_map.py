import folium
import json
import pandas as pd
import os

# Lire le CSV STEP03
df = pd.read_csv("csv\STEP03_maisons_dept29.csv")

# Créer un dict GPS -> nom de commune
commune_names = {}
prix = {}
taille = {}
pieces = {}
for index, row in df.iterrows():
    if pd.notna(row['GPS']) and row['GPS'] != '':
        lieu = row['Lieu']
        if pd.notna(lieu):
            parts = lieu.strip().rsplit(None, 1)
            if len(parts) == 2 and parts[1].isdigit() and len(parts[1]) == 5:
                ville = parts[0].strip().replace('-', ' ').upper()
                commune_names[row['GPS']] = ville
                prix[row['GPS']] = row['Prix']
                taille[row['GPS']] = row['Taille']
                pieces[row['GPS']] = row['Pieces']

# Filtrer les lignes avec GPS non vide et récupérer les valeurs uniques
unique_gps = df[df['GPS'].notna() & (df['GPS'] != '')]['GPS'].unique()

# Créer une carte centrée sur la Bretagne
m = folium.Map(location=[48.1, -3.15], zoom_start=8, tiles='CartoDB positron')

# Ajouter chaque GeoJSON unique à la carte
for gps in unique_gps:
    try:
        geojson_data = json.loads(gps)
        name = commune_names.get(gps, "Inconnu")
        folium.GeoJson(
            geojson_data, 
            name="Contour de la commune",
            tooltip=f"{name}<br>Prix: {prix.get(gps, 'N/A')}<br>Taille: {taille.get(gps, 'N/A')} m²<br>Pièces: {pieces.get(gps, 'N/A')}",
            style_function=lambda x: {'fillColor': 'lightgreen', 'color': 'green', 'weight': 2, 'fillOpacity': 0.3}
        ).add_to(m)
    except json.JSONDecodeError:
        print(f"Erreur de parsing JSON pour : {gps[:50]}...")

# Ajouter un contrôle des couches
folium.LayerControl().add_to(m)

# Sauvegarder la carte dans un fichier HTML
os.makedirs("map", exist_ok=True)
m.save("map/map.html")