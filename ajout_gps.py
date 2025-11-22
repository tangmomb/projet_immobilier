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

# Créer un dict pour lookup rapide : (Nom_de_la_commune (majuscule), Code_postal) -> {'insee': ..., 'geometry': ...}
gps_dict = {}
for _, row in df_gps.iterrows():
    commune = row['Nom_de_la_commune'].strip().upper()
    code_postal = str(row['Code_postal']).strip()
    insee = row['#Code_commune_INSEE']
    geometry = row['_contours_commune.geometry']
    key = (commune, code_postal)
    gps_dict[key] = {'insee': insee, 'geometry': geometry}

# Ajout des nouvelles colonnes
df_step02['Code INSEE'] = ''
df_step02['GPS'] = ''

# Pour chaque ligne dans STEP02
for index, row in df_step02.iterrows():
    lieu = row['Lieu']
    if pd.notna(lieu):
        # Extraire la ville et le code postal
        parts = lieu.strip().rsplit(None, 1)
        if len(parts) == 2 and parts[1].isdigit() and len(parts[1]) == 5:
            ville = parts[0].strip().replace('-', ' ').upper()
            code_postal = parts[1].strip()
            key = (ville, code_postal)
            if key in gps_dict:
                data = gps_dict[key]
                df_step02.at[index, 'Code INSEE'] = data['insee']
                df_step02.at[index, 'GPS'] = data['geometry']

# Écriture du nouveau CSV STEP03
output_path = step02_path.replace('STEP02', 'STEP03')
df_step02.to_csv(output_path, index=False)
print(f"Fichier STEP03 créé : {output_path}")