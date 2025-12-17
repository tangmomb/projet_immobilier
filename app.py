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
        
        # Légende des couleurs
        st.markdown("""
        <div style="width:100%; padding:2px 10px; background-color:white; margin-top:10px; margin-bottom:20px; color:gray;">
        <div style="display:flex; justify-content:flex-start; align-items:center;">
        <span style="margin-right:20px; font-weight:bold;">Prix moyen au m² :</span>
        <div style="display:flex; justify-content:space-around; align-items:center; flex:1;">
        <div style="display:flex; align-items:center; margin:5px;"><div style="width:20px; height:20px; background-color:#4CAF50; margin-right:5px; border-radius:50%;"></div> ≤ 1614.75 €</div>
        <div style="display:flex; align-items:center; margin:5px;"><div style="width:20px; height:20px; background-color:#FFC107; margin-right:5px; border-radius:50%;"></div> 1614.75 - 2062.0 €</div>
        <div style="display:flex; align-items:center; margin:5px;"><div style="width:20px; height:20px; background-color:#FF9800; margin-right:5px; border-radius:50%;"></div> 2062.0 - 2577.5 €</div>
        <div style="display:flex; align-items:center; margin:5px;"><div style="width:20px; height:20px; background-color:#F44336; margin-right:5px; border-radius:50%;"></div> > 2577.5 €</div>
        </div>
        </div>
        </div>
        """, unsafe_allow_html=True)
        
    except FileNotFoundError:
        st.error("Le fichier STEP06_map.html n'a pas été trouvé. Veuillez exécuter create_map.py d'abord.")


# Section de recherche avancée
with st.expander("Recherche avancée"):

    dept_options = ["Côtes d'Armor (22)", "Finistère (29)", "Ille-et-Vilaine (35)", "Morbihan (56)"]

    depts = {"22": "Côtes d'Armor (22)", "29": "Finistère (29)", "35": "Ille-et-Vilaine (35)", "56": "Morbihan (56)"}
    ville_to_dept = {}
    for dept_code in ["22", "29", "35", "56"]:
        try:
            df_comm = pd.read_csv(f"csv/STEP00/communes_dept{dept_code}.csv")
            for ville in df_comm['LIBELLE'].str.lower().unique():
                ville_to_dept[ville] = depts[dept_code]
        except:
            pass

    col_dept, col_ville = st.columns([2, 1])

    with col_ville:
        ville = st.text_input("Ville:")

    dept_defaults = [True] * 4
    if ville.strip():
        ville_lower = ville.strip().lower()
        if ville_lower in ville_to_dept:
            target_dept = ville_to_dept[ville_lower]
            dept_defaults = [opt == target_dept for opt in dept_options]

    with col_dept:
        st.write("Départements")
        dept_checks = [st.checkbox(opt, value=default) for opt, default in zip(dept_options, dept_defaults)]
        selected_depts = [opt for opt, checked in zip(dept_options, dept_checks) if checked]

    # Load data for selected departments
    if selected_depts:
        dfs = []
        for selected in selected_depts:
            dept = selected.split('(')[1].strip(')')
            csv_file = f"csv/STEP02/STEP02_maisons_dept{dept}.csv"
            try:
                df_temp = pd.read_csv(csv_file)
                dfs.append(df_temp)
            except FileNotFoundError:
                st.error(f"Le fichier {csv_file} n'a pas été trouvé.")
        if dfs:
            df = pd.concat(dfs, ignore_index=True)
        else:
            df = pd.DataFrame()
    else:
        st.warning("Veuillez sélectionner au moins un département.")
        df = pd.DataFrame()
    try:
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
        
        col_main1, col_main2 = st.columns(2)
        
        with col_main1:

            col1, col2, col3 = st.columns(3)
            with col1:
                st.write("Prix (€)")
                prix_0 = st.checkbox("0 - 100 000 €")
                prix_1 = st.checkbox("100 000 - 200 000 €")
                prix_2 = st.checkbox("200 000 - 300 000 €")
                prix_3 = st.checkbox("300 000 € et plus")
                checked_prix = [prix_0, prix_1, prix_2, prix_3]
                ranges_prix = [(0, 100000), (100000, 200000), (200000, 300000), (300000, int(prix_max))]
                if any(checked_prix):
                    selected_ranges = [r for c, r in zip(checked_prix, ranges_prix) if c]
                    min_prix = min(r[0] for r in selected_ranges)
                    max_prix = max(r[1] for r in selected_ranges)
                else:
                    min_prix = max_prix = None

            with col2:
                st.write("Taille (m²)")
                taille_0 = st.checkbox("0 - 100 m²")
                taille_1 = st.checkbox("100 - 200 m²")
                taille_2 = st.checkbox("200 - 300 m²")
                taille_3 = st.checkbox("300 m² et plus")
                checked_taille = [taille_0, taille_1, taille_2, taille_3]
                ranges_taille = [(0, 100), (100, 200), (200, 300), (300, int(taille_max))]
                if any(checked_taille):
                    selected_ranges = [r for c, r in zip(checked_taille, ranges_taille) if c]
                    min_taille = min(r[0] for r in selected_ranges)
                    max_taille = max(r[1] for r in selected_ranges)
                else:
                    min_taille = max_taille = None
            
            with col3 :
                st.write("Nombre de pièces")
                pieces_0 = st.checkbox("1 - 3 pièces")
                pieces_1 = st.checkbox("4 - 6 pièces")
                pieces_2 = st.checkbox("7 - 9 pièces")
                pieces_3 = st.checkbox("10 pièces et plus")
                checked_pieces = [pieces_0, pieces_1, pieces_2, pieces_3]
                ranges_pieces = [(1, 3), (4, 6), (7, 9), (10, int(pieces_max))]
                if any(checked_pieces):
                    selected_ranges = [r for c, r in zip(checked_pieces, ranges_pieces) if c]
                    min_pieces = min(r[0] for r in selected_ranges)
                    max_pieces = max(r[1] for r in selected_ranges)
                else:
                    min_pieces = max_pieces = None
        
        
        
        # Filtrer
        conditions = []
        if min_prix is not None:
            conditions.append(df['Prix'].notna() & (df['Prix'] >= min_prix) & (df['Prix'] <= max_prix))
        if min_taille is not None:
            conditions.append(df['Taille'].notna() & (df['Taille'] >= min_taille) & (df['Taille'] <= max_taille))
        if min_pieces is not None:
            conditions.append(df['Pieces'].notna() & (df['Pieces'] >= min_pieces) & (df['Pieces'] <= max_pieces))
        if conditions:
            combined_condition = conditions[0]
            for cond in conditions[1:]:
                combined_condition &= cond
            filtered = df[combined_condition]
        else:
            filtered = df
        
        if ville:
            filtered = filtered[filtered['Lieu'].str.contains(ville, case=False, na=False)]
        
        # Réorganiser les colonnes pour mettre Lien en dernier
        filtered = filtered[['Nom', 'Prix', 'Lieu', 'Taille', 'Taille_terrain', 'Pieces', 'Lien']]
        
        # Afficher
        st.dataframe(filtered, column_config={"Nom": st.column_config.TextColumn("Nom de l'annonce"), "Prix": st.column_config.NumberColumn("Prix €", format="%.0f"), "Taille": st.column_config.NumberColumn("Taille en m2", format="%.0f"), "Taille_terrain": st.column_config.NumberColumn("Taille du terrain en m2", format="%.0f"), "Pieces": st.column_config.NumberColumn("Nombre de pièces", format="%.0f"), "Lien": st.column_config.LinkColumn()})
        
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
