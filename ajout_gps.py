import pandas as pd

# Chemin du fichier de référence
gps_path = r"csv\laposte-hexasmal.csv"

# Demander le chemin du fichier CSV STEP02
step02_path = input("Entrez le chemin du fichier CSV STEP02 : ").strip()
if not step02_path:
    print("Chemin invalide.")
    exit()

# Lecture des CSVs
df_step02 = pd.read_csv(step02_path)
df_gps = pd.read_csv(gps_path)

# Créer un dict pour lookup rapide : Nom_de_la_commune (majuscule) -> {'insee': ..., 'geometry': ...}
gps_dict = {}
for _, row in df_gps.iterrows():
    commune = row['Nom_de_la_commune'].strip().upper()
    insee = row['#Code_commune_INSEE']
    geometry = row['_contours_commune.geometry']
    gps_dict[commune] = {'insee': insee, 'geometry': geometry}

# Ajout des nouvelles colonnes
df_step02['#Code_commune_INSEE'] = ''
df_step02['_contours_commune.geometry'] = ''

# Pour chaque ligne dans STEP02
for index, row in df_step02.iterrows():
    lieu = row['Lieu']
    if pd.notna(lieu):
        # Extraire la ville (premier mot, remplacer tirets par espaces, en majuscule)
        ville = lieu.split()[0].strip().replace('-', ' ').upper()
        if ville in gps_dict:
            data = gps_dict[ville]
            df_step02.at[index, '#Code_commune_INSEE'] = data['insee']
            df_step02.at[index, '_contours_commune.geometry'] = data['geometry']

# Écriture du nouveau CSV STEP03
output_path = step02_path.replace('STEP02', 'STEP03')
df_step02.to_csv(output_path, index=False)
print(f"Fichier STEP03 créé : {output_path}")