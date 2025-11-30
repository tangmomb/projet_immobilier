import pandas as pd
import os

# Chemin du fichier de référence
gps_path = r"csv\laposte-hexasmal.csv"

# Chemin du fichier à traiter
input_path = r"csv\all_bretagne.csv"

# Vérifier si le fichier existe
if not os.path.exists(input_path):
    print(f"Le fichier {input_path} n'existe pas.")
    exit()

# Lecture des CSVs
df_input = pd.read_csv(input_path)
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
df_input['Code INSEE'] = ''
df_input['GPS'] = ''

# Pour chaque ligne dans le fichier input
for index, row in df_input.iterrows():
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
                df_input.at[index, 'Code INSEE'] = data['insee']
                df_input.at[index, 'GPS'] = data['geometry']

# Écriture du nouveau CSV
output_path = input_path.replace('.csv', '_with_gps.csv')
df_input.to_csv(output_path, index=False)
print(f"Fichier avec GPS créé : {output_path}")