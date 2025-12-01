import os
import pandas as pd

data_dir = os.path.join(os.path.dirname(__file__), '..', 'csv')

# Process each CSV file starting with 'STEP02'
for file in os.listdir(data_dir):
    if file.startswith('STEP02') and file.endswith('.csv'):
        path = os.path.join(data_dir, file)
        df = pd.read_csv(path)
        
        # Nettoyage numérique
        df['Taille'] = pd.to_numeric(df['Taille'].astype(str).str.replace(' ', ''), errors='coerce')
        df['Prix'] = pd.to_numeric(df['Prix'].astype(str).str.replace(' ', ''), errors='coerce')
        
        # Assuming columns 'Prix' (price) and 'Taille' (area in m²)
        # Calculate 'Prix au m2'
        df['Prix au m2'] = df['Prix'] / df['Taille']
        
        # Arrondir à l'entier
        df['Prix au m2'] = df['Prix au m2'].round(0)
        
        # Save the updated DataFrame back to the same file
        df.to_csv(path, index=False)