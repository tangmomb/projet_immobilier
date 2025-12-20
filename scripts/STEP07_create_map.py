import folium
from folium.plugins import HeatMap
import geopandas as gpd
import json
import pandas as pd
import os

# Lire le CSV all_bretagne_with_gps
csv_file = 'csv/STEP06/STEP06_all_bretagne_with_gps.csv'
if not os.path.exists(csv_file):
    print(f"Le fichier {csv_file} n'existe pas.")
    exit(1)

df = pd.read_csv(csv_file)

# Filtrer les lignes avec GPS non vide
df = df[df['GPS'].notna() & (df['GPS'] != '')]

# Calculer les valeurs min et max pour la normalisation des couleurs
valid_avgs = df['Prix moyen au m2'].dropna()
if not valid_avgs.empty:
    q1, q2, q3 = valid_avgs.quantile([0.25, 0.5, 0.75])
    print(f"Q1 (25%): {q1}")
    print(f"Q2 (50%): {q2}")
    print(f"Q3 (75%): {q3}")
else:
    q1 = q2 = q3 = 0  # dummy

# Créer une carte centrée sur la Bretagne
m = folium.Map(location=[48.1, -3.15], zoom_start=8, tiles='CartoDB positron')

# Ajouter chaque GeoJSON à la carte
for index, row in df.iterrows():
    try:
        geojson_data = json.loads(row['GPS'])
        lieu = row['Ville']
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
        
        # Calculer la couleur basée sur les quartiles du prix moyen
        if pd.notna(avg_price):
            if avg_price <= q1:
                fill_color = '#4CAF50'  
            elif avg_price <= q2:
                fill_color = '#FFC107'  
            elif avg_price <= q3:
                fill_color = '#FF9800'  
            else:
                fill_color = '#F44336'  
        else:
            fill_color = 'gray'
        
        folium.GeoJson(
            geojson_data, 
            name="Contour de la commune",
            tooltip=f"<div style='font-size: 16px; padding: 10px; background-color: white; border: 1px solid black; border-radius: 5px;'>{name}<br>Maisons à vendre: {count}<br>Prix moyen/m²: {avg_price if pd.notna(avg_price) else 'N/A'} €</div>",
            style_function=lambda x, color=fill_color: {'fillColor': color, 'color': "#CCCCCC", 'weight': 2, 'fillOpacity': 0.8}
        ).add_to(m)
    except json.JSONDecodeError:
        print(f"Erreur de parsing JSON pour : {row['GPS'][:50]}...")


# Sauvegarder la carte dans un fichier HTML
m.save("STEP07_map_prix.html")



# ----------------------------------------
# Seconde carte heatmap
# ----------------------------------------

# Utiliser le même DataFrame filtré que pour la première carte
# Convertir la colonne GPS (GeoJSON) en géometrie
df['geometry'] = df['GPS'].apply(lambda x: gpd.GeoSeries.from_file(json.dumps(json.loads(x))).geometry[0] if x else None)

# Créer un GeoDataFrame
gdf = gpd.GeoDataFrame(df, geometry='geometry')

# calcul du point central de chaque géométrie du Dataframe et transformation des polygones/lignes, en points
gdf['centroid'] = gdf.geometry.centroid
gdf_points = gdf.set_geometry('centroid')

# Coordonnées approximatives du centre (ici Bretagne)
map_center = [48.1, -3.15]
m = folium.Map(location=map_center, zoom_start=8, tiles='CartoDB positron')

# Préparer les points pour la heatmap (lat, lon, poids)
heat_data = [[point.y, point.x, nb] for point, nb in zip(gdf_points.geometry, gdf_points['Nombre de maisons à vendre'])]

# Ajouter la heatmap
HeatMap(heat_data, radius=12).add_to(m)

# Afficher la carte
m.save("STEP07_map_densite.html")