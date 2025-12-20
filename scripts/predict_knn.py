import pandas as pd
import numpy as np
from sklearn.neighbors import NearestNeighbors
import glob
import warnings

warnings.filterwarnings("ignore", category=RuntimeWarning)

def load_insee_codes():
    # Charger le fichier des codes INSEE
    df_insee = pd.read_csv("csv/code_insee.csv", dtype=str)
    # Filtrer pour la Bretagne (départements 22, 29, 35, 56)
    df_insee = df_insee[df_insee['DEP'].isin(['22', '29', '35', '56'])]
    return df_insee

def get_insee_code(commune_name, df_insee):
    # Normaliser pour matcher NCC (majuscules, - remplacé par espace)
    def normalize(s):
        if pd.isna(s):
            return ""
        s = str(s).upper()
        s = s.replace('-', ' ')
        return s
    
    commune_norm = normalize(commune_name)
    match = df_insee[df_insee['NCC'].apply(lambda x: str(x).replace('-', ' ')) == commune_norm]
    if not match.empty:
        return int(match.iloc[0]['COM'])
    else:
        raise ValueError(f"Commune '{commune_name}' non trouvée dans les données INSEE.")

def load_knn_data():
    # --- Charger tous les CSV du dossier STEP02 (avant imputation) ---
    files = glob.glob("csv/STEP02/STEP02_maisons_dept*.csv")
    df_list = []
    for file in files:
        df_temp = pd.read_csv(file)
        df_list.append(df_temp)
    df = pd.concat(df_list, ignore_index=True)

    # --- Nettoyer les colonnes numériques ---
    numeric_cols = ["Taille", "Taille_terrain", "Pieces", "Prix"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(' ', ''), errors='coerce')

    # Supprimer les lignes où Taille est NaN
    df = df.dropna(subset=["Taille"])
    
    print(f"Total maisons chargées : {len(df)}")
    return df

def knn_estimation(df, ville, taille, terrain=None, pieces=None, k=2, max_distance=None):
    # Features numériques utilisées pour la distance
    features = ["Taille"]
    if terrain is not None:
        features.append("Taille_terrain")
    if pieces is not None:
        features.append("Pieces")
    
    # Filtrer la ville
    df_ville = df[df["Code INSEE"] == ville].copy()
    if df_ville.empty:
        return None, "Ville non trouvée dans le dataset", None
    
    # Garder seulement les maisons avec les features requises non manquantes
    df_ville = df_ville.dropna(subset=features)
    if df_ville.empty:
        return None, f"Aucune maison dans cette ville avec les features requises ({', '.join(features)})", None
    
    # Vérifier si une maison très similaire existe
    exact_match = df_ville[(df_ville['Taille'] == taille)]
    if terrain is not None:
        exact_match = exact_match[exact_match['Taille_terrain'] == terrain]
    if pieces is not None:
        exact_match = exact_match[exact_match['Pieces'] == pieces]
    if not exact_match.empty:
        print(f"Maison très similaire trouvée : {exact_match.iloc[0]['Nom']} - Prix : {exact_match.iloc[0]['Prix']}")
        # Retourner le prix exact et la maison très similaire
        exact_house = exact_match.iloc[0][["Nom", "Lieu", "Pieces", "Taille", "Taille_terrain", "Prix", "Lien"]].to_dict()
        return exact_match.iloc[0]['Prix'], [exact_house], len(df_ville), None
    else:
        print("Aucune maison très similaire trouvée avec ces valeurs.")
    
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
    
    # Filtrer les voisins dans la tolérance de distance
    if max_distance is not None:
        valid_mask = distances[0] <= max_distance
        valid_indices = indices[0][valid_mask]
        valid_distances = distances[0][valid_mask]
        if len(valid_indices) == 0:
            return None, f"Aucune maison suffisamment proche (distance euclidienne de la plus proche : {distances[0][0]:.2f}, supérieure à la limite donnée de {max_distance}).", len(df_ville), None
        # Prendre jusqu'à k voisins valides
        num_neighbors = min(k, len(valid_indices))
        selected_indices = valid_indices[:num_neighbors]
        selected_distances = valid_distances[:num_neighbors]
    else:
        selected_indices = indices[0]
        selected_distances = distances[0]
        num_neighbors = len(selected_indices)
    
    # Moyenne des prix
    prix_estime = df_ville.iloc[selected_indices]["Prix"].mean()
    
    # Données des maisons les plus proches
    houses_data = df_ville.iloc[selected_indices][["Nom", "Lieu", "Pieces", "Taille", "Taille_terrain", "Prix", "Lien"]].to_dict('records')
    
    return prix_estime, houses_data, len(df_ville), None

# --- Exemple d'utilisation ---
if __name__ == "__main__":
    # Charger les codes INSEE
    df_insee = load_insee_codes()
    
    # Demander le nom de la commune
    commune_name = input("Entrez le nom de la commune : ")
    try:
        ville_code_insee = get_insee_code(commune_name, df_insee)
        print(f"Code INSEE trouvé : {ville_code_insee}")
    except ValueError as e:
        print(e)
        exit(1)
    
    taille_maison = int(input("Entrez la taille de la maison (m²) : "))
    terrain_input = input("Entrez la taille du terrain (m²) ou laissez vide : ").strip()
    terrain_maison = int(terrain_input) if terrain_input else None
    pieces_input = input("Entrez le nombre de pièces ou laissez vide : ").strip()
    pieces_maison = int(pieces_input) if pieces_input else None
    
    df = load_knn_data()
    prix, maisons, num_maisons, _ = knn_estimation(df, ville_code_insee, taille_maison, terrain_maison, pieces_maison, k=2, max_distance=30)    
    if prix is not None:
        print(f"Prix estimé : {prix:,.0f} €")
        print(f"Nombre de maisons dans la commune : {num_maisons}")
        if len(maisons) == 1:
            print("Maison la plus proche :")
        else:
            print("Maisons les plus proches :")
        for house in maisons:
            print(f"- {house['Nom']} - Prix : {house['Prix']} - Taille : {house['Taille']} m² - Terrain : {house['Taille_terrain']} m² - Pièces : {house['Pieces']}")
    else:
        print("Erreur :", maisons)