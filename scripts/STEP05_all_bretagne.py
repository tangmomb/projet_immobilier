import pandas as pd
import glob
import os

# Créer le dossier de sortie si nécessaire
os.makedirs('csv/STEP05', exist_ok=True)

# Trouver tous les fichiers CSV contenant "STEP04" dans le nom
files = glob.glob("csv/STEP04/*STEP04*.csv")

# Liste pour stocker les DataFrames
dfs = []

# Lire chaque fichier CSV (supposant des colonnes : 'ville', 'nb_maisons', 'prix_m2')
for file in files:
    df = pd.read_csv(file)
    dfs.append(df)

# Concaténer tous les DataFrames
all_data = pd.concat(dfs, ignore_index=True)

# Nettoyer et convertir les colonnes
all_data['Prix_num'] = pd.to_numeric(all_data['Prix'].astype(str).str.replace(' ', '').str.replace('€', ''), errors='coerce')
all_data['Taille_num'] = pd.to_numeric(all_data['Taille'].astype(str).str.replace(' ', '').str.replace('m²', ''), errors='coerce')

# Calculer le prix au m²
all_data['prix_m2'] = all_data['Prix_num'] / all_data['Taille_num']

# Grouper par Lieu, compter les maisons, moyenner le prix au m²
result = all_data.groupby('Code INSEE').agg({
    'Lien': 'count',
    'prix_m2': 'mean',
    'Lieu': 'first'
}).reset_index()

# Renommer les colonnes
result.rename(columns={'Lien': 'Nombre de maisons à vendre', 'prix_m2': 'Prix moyen au m2', 'Lieu': 'Ville'}, inplace=True)

# Convertir Code INSEE en string sans .0
result['Code INSEE'] = result['Code INSEE'].astype(int).astype(str)

# Arrondir le prix moyen à l'entier le plus proche
result['Prix moyen au m2'] = result['Prix moyen au m2'].round().astype('Int64')

# Écrire dans un nouveau CSV
result.to_csv('csv/STEP05/STEP05_all_bretagne.csv', index=False)