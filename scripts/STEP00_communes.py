# Extraire toutes les villes du département depuis code_insee.csv et créer un nouveau CSV
import pandas as pd
import sys

# Charger le fichier code_insee.csv
df_insee = pd.read_csv('../csv/code_insee.csv', encoding='utf-8')

# Demander le numéro du département
dept = input("Numéro du département : ").strip()
if not dept.isdigit() or len(dept) < 1 or len(dept) > 3:
    print("Numéro de département invalide. Arrêt du script.")
    sys.exit(1)

# Filtrer pour le département
df_dept = df_insee[df_insee['DEP'] == dept]

# Sauvegarder dans un nouveau CSV
df_dept.to_csv(f'../csv/STEP00/communes_dept{dept}.csv', index=False, encoding='utf-8')

print(f"Nombre de communes dans le département {dept}: {len(df_dept)}")
print(f"Nouveau CSV créé: ../csv/STEP00/communes_dept{dept}.csv")