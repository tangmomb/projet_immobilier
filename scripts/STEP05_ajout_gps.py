import pandas as pd
import os

# Créer le dossier de sortie si nécessaire
os.makedirs(r"csv\STEP05", exist_ok=True)

# Chemin du fichier de référence
gps_path = r"csv\laposte-hexasmal.csv"

# Chemin du fichier à traiter
input_path = r"csv\STEP04\STEP04_all_bretagne.csv"

# Vérifier si le fichier existe
if not os.path.exists(input_path):
    print(f"Le fichier {input_path} n'existe pas.")
    exit()

# Lecture des CSVs
df_input = pd.read_csv(input_path)
df_gps = pd.read_csv(gps_path)

# Créer un dict pour lookup rapide : Code_commune_INSEE -> geometry
gps_dict = {}
for _, row in df_gps.iterrows():
    insee_str = str(row['#Code_commune_INSEE'])
    if insee_str.isdigit():
        insee = int(insee_str)
        geometry = row['_contours_commune.geometry']
        gps_dict[insee] = geometry

# Ajout de la colonne GPS
df_input['GPS'] = ''

# Compteur pour debug
count = 0

# Pour chaque ligne dans le fichier input
for index, row in df_input.iterrows():
    code_str = str(row['Code INSEE'])
    if code_str.isdigit():
        code_insee = int(code_str)
        geometry = gps_dict.get(code_insee, '')
        df_input.at[index, 'GPS'] = geometry
        if geometry != '':
            count += 1

# Écriture du nouveau CSV
output_filename = "STEP05_all_bretagne_with_gps.csv"
output_path = os.path.join(r"csv\STEP05", output_filename)
df_input.to_csv(output_path, index=False)
print(f"Fichier avec GPS créé : {output_path}")
print(f"GPS trouvé pour {count} communes sur {len(df_input)}")