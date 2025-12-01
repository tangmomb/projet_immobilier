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
        df_agg = pd.read_csv("csv/STEP04/STEP04_all_bretagne.csv")
        if 'reset_search' not in st.session_state:
            st.session_state['reset_search'] = False
        search = st.text_input("Rechercher une ville:", value="" if st.session_state['reset_search'] else None)
        if st.session_state['reset_search']:
            st.session_state['reset_search'] = False
        if st.button("Réinitialiser la recherche"):
            st.session_state['reset_search'] = True
        if search:
            filtered_df = df_agg[df_agg['Ville'].str.contains(search, case=False, na=False)]
        else:
            filtered_df = df_agg
        # Réorganiser les colonnes : Ville, Nombre de maisons à vendre, Prix moyen au m2
        filtered_df = filtered_df[['Ville', 'Nombre de maisons à vendre', 'Prix moyen au m2']]
        st.write("Ville / Maisons en vente / Prix moyen au m2")
        st.write(f'<div style="height:400px; overflow-y:scroll;">{filtered_df.to_html(index=False, header=False)}</div>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.error("Le fichier csv/all_bretagne.csv n'a pas été trouvé. Veuillez exécuter all_bretagne.py d'abord.")

# Colonne droite : carte
with col2:
    try:
        with open("STEP06_map.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        components.html(html_content, height=600)
    except FileNotFoundError:
        st.error("Le fichier STEP06_map.html n'a pas été trouvé. Veuillez exécuter create_map.py d'abord.")


# Section de recherche avancée
with st.expander("Recherche avancée"):

    dept_options = ["Côtes d'Armor (22)", "Finistère (29)", "Ille-et-Vilaine (35)", "Morbihan (56)"]

    col_dept, col_ville = st.columns([2, 1])

    with col_dept:
        selected = st.radio("Département", dept_options, horizontal=True)

    with col_ville:
        ville = st.text_input("Ville:")

    dept = selected.split('(')[1].strip(')')

    csv_file = f"csv/STEP02/STEP02_maisons_dept{dept}.csv"

    try:
        df = pd.read_csv(csv_file)
        
        # Nettoyer les données
        df['Prix'] = pd.to_numeric(df['Prix'].astype(str).str.replace(' ', '').str.replace('€', ''), errors='coerce')
        df['Taille'] = pd.to_numeric(df['Taille'].astype(str).str.replace(' ', ''), errors='coerce')
        df['Taille_terrain'] = pd.to_numeric(df['Taille_terrain'].astype(str).str.replace(' ', ''), errors='coerce')
        df['Pieces'] = pd.to_numeric(df['Pieces'].astype(str).str.replace(' ', ''), errors='coerce')
        
        # Filtres
        prix_min = df['Prix'].dropna().min() if not df['Prix'].dropna().empty else 0
        prix_max = df['Prix'].dropna().max() if not df['Prix'].dropna().empty else 1000000
        taille_min = df['Taille'].dropna().min() if not df['Taille'].dropna().empty else 0
        taille_max = df['Taille'].dropna().max() if not df['Taille'].dropna().empty else 1000
        pieces_min = df['Pieces'].dropna().min() if not df['Pieces'].dropna().empty else 1
        pieces_max = df['Pieces'].dropna().max() if not df['Pieces'].dropna().empty else 10
        
        col_prix, col_taille, col_pieces = st.columns(3)
        
        with col_prix:
            min_prix, max_prix = st.slider("Prix (€)", min_value=0, max_value=int(prix_max), value=(int(prix_min), int(prix_max)))
        
        with col_taille:
            min_taille, max_taille = st.slider("Taille (m²)", min_value=0, max_value=int(taille_max), value=(int(taille_min), int(taille_max)))
        
        with col_pieces:
            min_pieces, max_pieces = st.slider("Nombre de pièces", min_value=0, max_value=int(pieces_max), value=(int(pieces_min), int(pieces_max)))
        
        # Filtrer
        filtered = df[
            (df['Prix'].notna() & (df['Prix'] >= min_prix) & (df['Prix'] <= max_prix)) &
            (df['Taille'].notna() & (df['Taille'] >= min_taille) & (df['Taille'] <= max_taille)) &
            (df['Pieces'].notna() & (df['Pieces'] >= min_pieces) & (df['Pieces'] <= max_pieces))
        ]
        
        if ville:
            filtered = filtered[filtered['Lieu'].str.contains(ville, case=False, na=False)]
        
        # Réorganiser les colonnes pour mettre Lien en dernier
        filtered = filtered[['Nom', 'Prix', 'Lieu', 'Taille', 'Taille_terrain', 'Pieces', 'Lien']]
        
        # Afficher
        st.dataframe(filtered, column_config={"Nom": st.column_config.TextColumn("Nom de l'annonce"), "Prix": st.column_config.NumberColumn("Prix €", format="%.0f"), "Taille": st.column_config.NumberColumn("Taille en m2", format="%.0f"), "Taille_terrain": st.column_config.NumberColumn("Taille du terrain en m2", format="%.0f"), "Pieces": st.column_config.NumberColumn("Nombre de pièces", format="%.0f"), "Lien": st.column_config.LinkColumn()})
        
    except FileNotFoundError:
        st.error(f"Le fichier {csv_file} n'a pas été trouvé.")
    except Exception as e:
        st.error(f"Erreur lors du chargement des données: {e}")

# Section de statistiques
with st.expander("Statistiques des prix immobiliers"):
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
        
        # Charger les données
        df_stats = pd.read_csv("csv/STEP05/STEP05_all_bretagne_with_gps.csv")
        df_stats = df_stats[df_stats['GPS'].notna() & (df_stats['GPS'] != '')]
        prix = df_stats['Prix moyen au m2'].dropna()
        
        # Afficher les statistiques
        st.write("**Valeurs statistiques des prix moyens au m² :**")
        col_min, col_q1, col_med, col_q3, col_max = st.columns(5)
        with col_min:
            st.metric("Minimum", f"{prix.min():.0f} €")
        with col_q1:
            st.metric("Q1 (25%)", f"{prix.quantile(0.25):.0f} €")
        with col_med:
            st.metric("Médiane", f"{prix.quantile(0.5):.0f} €")
        with col_q3:
            st.metric("Q3 (75%)", f"{prix.quantile(0.75):.0f} €")
        with col_max:
            st.metric("Maximum", f"{prix.max():.0f} €")
        
        # Afficher le boxplot
        st.write("**Distribution des prix (sans outliers) :**")
        fig, ax = plt.subplots(figsize=(8, 4))
        sns.boxplot(data=prix, orient='h', showfliers=False, ax=ax)
        ax.set_xlabel('Prix au m² (€)')
        st.pyplot(fig)
        
    except FileNotFoundError:
        st.error("Le fichier csv/STEP05/STEP05_all_bretagne_with_gps.csv n'a pas été trouvé.")
    except Exception as e:
        st.error(f"Erreur lors du chargement des statistiques: {e}")
