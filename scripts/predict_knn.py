import pandas as pd
import numpy as np
from sklearn.neighbors import NearestNeighbors
import glob

def load_knn_data():
    # --- Charger tous les CSV du dossier STEP04 ---
    files = glob.glob("csv/STEP04/STEP04_maisons_dept*.csv")
    df_list = []
    for file in files:
        df_temp = pd.read_csv(file)
        df_list.append(df_temp)
    df = pd.concat(df_list, ignore_index=True)

    # --- Nettoyer les colonnes numériques ---
    numeric_cols = ["Taille", "Taille_terrain", "Pieces", "Prix"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(' ', ''), errors='coerce')

    # --- Imputer Pieces et Taille_terrain par médiane de la commune ---
    df["Pieces"] = df.groupby("Code INSEE")["Pieces"].transform(lambda x: x.fillna(x.median()))
    df["Taille_terrain"] = df.groupby("Code INSEE")["Taille_terrain"].transform(lambda x: x.fillna(x.median()))
    
    return df

# --- Fonction KNN local ---
def knn_estimation(df, ville, taille, terrain=None, pieces=None, k=2, max_distance=None):
    # Filtrer la ville
    df_ville = df[df["Code INSEE"] == ville].copy()
    if df_ville.empty:
        return None, "Ville non trouvée dans le dataset"
    
    # Features numériques utilisées pour la distance
    features = ["Taille"]
    if terrain is not None:
        features.append("Taille_terrain")
    if pieces is not None:
        features.append("Pieces")
    
    # Construire la matrice X
    X = df_ville[features].values
    nbrs = NearestNeighbors(n_neighbors=min(k, len(X)), algorithm='auto').fit(X)
    
    # Construire le point à prédire
    point = np.array([[taille]])
    if terrain is not None:
        point = np.hstack([point, [[terrain]]])
    if pieces is not None:
        point = np.hstack([point, [[pieces]]])
    
    # Trouver les k plus proches voisins
    distances, indices = nbrs.kneighbors(point)
    
    # Vérifier la tolérance de proximité
    if max_distance is not None and distances[0].max() > max_distance:
        return None, f"Aucune maison suffisamment proche (distance max: {distances[0].max():.2f})"
    
    # Moyenne des prix
    prix_estime = df_ville.iloc[indices[0]]["Prix"].mean()
    
    # Données des maisons les plus proches
    houses_data = df_ville.iloc[indices[0]][["Nom", "Lieu", "Pieces", "Taille", "Taille_terrain", "Prix", "Lien"]].to_dict('records')
    
    return prix_estime, houses_data

# --- Exemple d'utilisation ---
ville_code_insee = 22001  # Code INSEE de la commune (entier)
taille_maison = 476          # m²
terrain_maison = 8848         # m²
pieces_maison = 21            # nombre de pièces

df = load_knn_data()
prix, maisons = knn_estimation(df, ville_code_insee, taille_maison, terrain_maison, pieces_maison, k=2, max_distance=500)
if prix is not None:
    print(f"Prix estimé : {prix:,.0f} €")
    print("Maisons les plus proches :")
    for maison in maisons:
        print(f"- {maison['Nom']}: {maison['Lien']}")
else:
    print(" Erreur :", maisons)
