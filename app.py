import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

st.set_page_config(layout="wide")

st.title("Carte des maisons à vendre en Bretagne")

# Créer deux colonnes : gauche 1/4, droite 3/4
col1, col2 = st.columns([1, 3])

# Colonne gauche : tableau avec recherche
with col1:
    # Afficher les données agrégées
    try:
        df_agg = pd.read_csv("csv/all_bretagne.csv")
        if 'reset_search' not in st.session_state:
            st.session_state['reset_search'] = False
        search = st.text_input("Rechercher une ville:", value="" if st.session_state['reset_search'] else None)
        if st.session_state['reset_search']:
            st.session_state['reset_search'] = False
        if st.button("Réinitialiser la recherche"):
            st.session_state['reset_search'] = True
        if search:
            filtered_df = df_agg[df_agg['Lieu'].str.contains(search, case=False, na=False)]
        else:
            filtered_df = df_agg
        st.write("Lieu, Maisons en vente, Prix moyen au m2")
        st.write(filtered_df.to_html(index=False, header=False), unsafe_allow_html=True)
    except FileNotFoundError:
        st.error("Le fichier csv/all_bretagne.csv n'a pas été trouvé. Veuillez exécuter all_bretagne.py d'abord.")

# Colonne droite : carte
with col2:
    try:
        with open("map/map.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        components.html(html_content, height=600)
    except FileNotFoundError:
        st.error("Le fichier map/map.html n'a pas été trouvé. Veuillez exécuter create_map.py d'abord.")

# Section de recherche avancée
st.header("Recherche avancée")

dept = st.selectbox("Département", ["22", "29"])

if dept == "22":
    csv_file = "csv/STEP01_maisons_dept22.csv"
elif dept == "29":
    csv_file = "csv/STEP02_maisons_dept29.csv"

try:
    df = pd.read_csv(csv_file)
    
    # Nettoyer les données
    df['Prix'] = pd.to_numeric(df['Prix'].str.replace(' ', '').str.replace('€', ''), errors='coerce')
    df['Taille'] = pd.to_numeric(df['Taille'], errors='coerce')
    df['Pieces'] = pd.to_numeric(df['Pieces'], errors='coerce')
    
    # Filtres
    prix_min = df['Prix'].dropna().min() if not df['Prix'].dropna().empty else 0
    prix_max = df['Prix'].dropna().max() if not df['Prix'].dropna().empty else 1000000
    taille_min = df['Taille'].dropna().min() if not df['Taille'].dropna().empty else 0
    taille_max = df['Taille'].dropna().max() if not df['Taille'].dropna().empty else 1000
    pieces_min = df['Pieces'].dropna().min() if not df['Pieces'].dropna().empty else 1
    pieces_max = df['Pieces'].dropna().max() if not df['Pieces'].dropna().empty else 10
    
    min_prix, max_prix = st.slider("Prix (€)", min_value=int(prix_min), max_value=int(prix_max), value=(int(prix_min), int(prix_max)))
    min_taille, max_taille = st.slider("Taille (m²)", min_value=int(taille_min), max_value=int(taille_max), value=(int(taille_min), int(taille_max)))
    min_pieces, max_pieces = st.slider("Nombre de pièces", min_value=int(pieces_min), max_value=int(pieces_max), value=(int(pieces_min), int(pieces_max)))
    
    # Filtrer
    filtered = df[
        (df['Prix'].notna() & (df['Prix'] >= min_prix) & (df['Prix'] <= max_prix)) &
        (df['Taille'].notna() & (df['Taille'] >= min_taille) & (df['Taille'] <= max_taille)) &
        (df['Pieces'].notna() & (df['Pieces'] >= min_pieces) & (df['Pieces'] <= max_pieces))
    ]
    
    # Afficher
    st.dataframe(filtered, column_config={"Lien": st.column_config.LinkColumn()})
    
except FileNotFoundError:
    st.error(f"Le fichier {csv_file} n'a pas été trouvé.")
except Exception as e:
    st.error(f"Erreur lors du chargement des données: {e}")
