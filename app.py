import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from sklearn.neighbors import NearestNeighbors
import numpy as np
import glob
from scripts.predict_knn import load_knn_data, knn_estimation, load_insee_codes, get_insee_code

# Couleurs de l'application (utilisables partout)
background_color = "#08131F"
border_color = "#1A4879"
text_highlight_color = "#239CFF"

st.set_page_config(layout="wide")

st.title("Marché de l'immobilier en Bretagne")

try:
    # Charger les cartes
    with open("maps/STEP07_map_prix.html", "r", encoding="utf-8") as f:
        prix_html = f.read()
    with open("maps/STEP07_map_densite.html", "r", encoding="utf-8") as f:
        densite_html = f.read()
    
    # Afficher en 2 colonnes
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Carte des prix moyens au m²")
        components.html(prix_html, height=600)
        
        # Légende des couleurs
        legend_html = """
        <div style="width:100%; padding:2px 10px; background-color:{background_color}; margin-top:10px; margin-bottom:20px; color:white; border:1px solid {border_color};">
        <div style="display:flex; justify-content:flex-start; align-items:center;">
        <span style="margin-right:20px; font-weight:bold; color:{text_highlight_color};">Prix moyen au m² :</span>
        <div style="display:flex; justify-content:space-around; align-items:center; flex:1;">
        <div style="display:flex; align-items:center; margin:5px;"><div style="width:20px; height:20px; background-color:#4CAF50; margin-right:5px; border-radius:50%;"></div> ≤ 1631.5 €</div>
        <div style="display:flex; align-items:center; margin:5px;"><div style="width:20px; height:20px; background-color:#FFC107; margin-right:5px; border-radius:50%;"></div> 1631.5 - 2071.0 €</div>
        <div style="display:flex; align-items:center; margin:5px;"><div style="width:20px; height:20px; background-color:#FF9800; margin-right:5px; border-radius:50%;"></div> 2071.0 - 2573.5 €</div>
        <div style="display:flex; align-items:center; margin:5px;"><div style="width:20px; height:20px; background-color:#F44336; margin-right:5px; border-radius:50%;"></div> > 2573.5 €</div>
        </div>
        </div>
        </div>
        """.format(background_color=background_color, border_color=border_color, text_highlight_color=text_highlight_color)
        st.markdown(legend_html, unsafe_allow_html=True)
    
    with col2:
        st.subheader("Carte de densité des maisons à vendre")
        components.html(densite_html, height=600)
        
except FileNotFoundError:
    st.error("Les fichiers maps/STEP07_map_prix.html et/ou maps/STEP07_map_densite.html n'ont pas été trouvés. Veuillez exécuter STEP07_create_map.py d'abord.")


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

    def clear_ville():
        st.session_state.ville_input = ""

    if "ville_input" not in st.session_state:
        st.session_state.ville_input = ""

    col_dept, col_ville = st.columns([2, 1])

    with col_ville:
        ville = st.text_input("Ville:", value=st.session_state.ville_input, key="ville_input")
        st.button("Effacer", on_click=clear_ville)

    dept_defaults = [True] * 4
    if st.session_state.ville_input.strip():
        ville_lower = st.session_state.ville_input.strip().lower()
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
            csv_file = f"csv/STEP04/STEP04_maisons_dept{dept}.csv"
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
        
        with col_main2:
            st.markdown(f"""
            <div style="background-color: {background_color};
                        padding: 15px;
                        border: 1px solid {border_color};
                        text-align: center;
                        font-size: 18px;
                        font-weight: bold;
                        color: rgb(255 255 255);">
            Nombre de maisons selon les critères sélectionnés : <br><span style="font-size: 28px; color: {text_highlight_color}; font-weight: 400;">{len(filtered)}</span>
            </div>
            """, unsafe_allow_html=True)
            
        
        

        
        # Réorganiser les colonnes pour mettre Lien en dernier
        filtered = filtered[['Nom', 'Prix', 'Lieu', 'Taille', 'Taille_terrain', 'Pieces', 'Lien']]
        
        # Afficher
        st.dataframe(filtered, hide_index=True, column_config={"Nom": st.column_config.TextColumn("Nom de l'annonce"), "Prix": st.column_config.NumberColumn("Prix €", format="%.0f"), "Taille": st.column_config.NumberColumn("Taille en m2", format="%.0f"), "Taille_terrain": st.column_config.NumberColumn("Taille du terrain en m2", format="%.0f"), "Pieces": st.column_config.NumberColumn("Nombre de pièces", format="%.0f"), "Lien": st.column_config.LinkColumn()})
        
    except Exception as e:
        st.error(f"Erreur lors du chargement des données: {e}")

# Section de statistiques
with st.expander("Statistiques des prix immobiliers"):
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
        
        # Charger les données
        df_graph = pd.read_csv("csv/STEP05/STEP05_all_bretagne.csv")
        
        # Ajouter la colonne departement
        df_graph["departement"] = df_graph["Code INSEE"].astype(str).str.zfill(5).str[:2]
        
        # Duplication des lignes pour pondérer les données dans le violin plot
        df_rep = df_graph.loc[df_graph.index.repeat(df_graph["Nombre de maisons à vendre"])]
        
        # Histogramme
        fig1, ax1 = plt.subplots(figsize=(10,6))
        ax1.hist(
            df_graph["Prix moyen au m2"],
            bins=20,
            weights=df_graph["Nombre de maisons à vendre"],
            edgecolor="black"
        )
        ax1.set_xlabel("Prix au m² (€)")
        ax1.set_ylabel("Nombre de maisons")
        ax1.set_title("Distribution du prix au m² (pondérée par le nombre de maisons)")
        
        # Violin plot
        fig2, ax2 = plt.subplots(figsize=(12,6))
        sns.violinplot(
            x="departement",
            y="Prix moyen au m2",
            data=df_rep,
            inner="quartile",
            palette="Set2",
            cut=0,
            ax=ax2
        )
        ax2.set_xlabel("Département")
        ax2.set_ylabel("Prix au m² (€)")
        ax2.set_title("Distribution du prix au m² par département")
        
        # Scatter plot
        fig3, ax3 = plt.subplots(figsize=(10,6))
        sns.scatterplot(
            data=df_graph,
            x="Nombre de maisons à vendre",
            y="Prix moyen au m2",
            hue="departement",
            palette="Set1",
            alpha=0.8,
            ax=ax3
        )
        ax3.set_title("Prix au m² vs nombre de maisons (par département)")
        
        # Présenter en 3 colonnes
        col1, col2, col3 = st.columns(3)
        with col1:
            st.pyplot(fig1)
            st.markdown(f"""
            <div style="background-color: {background_color}; padding: 10px; border: 1px solid {border_color}; color: white; margin-top: 10px;">
            Cet histogramme montre la distribution des prix au m² pondérée par le nombre de maisons à vendre, permettant de voir la répartition globale des prix en Bretagne.
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.pyplot(fig2)
            st.markdown(f"""
            <div style="background-color: {background_color}; padding: 10px; border: 1px solid {border_color}; color: white; margin-top: 10px;">
            Le violin plot illustre la distribution des prix au m² par département, avec une pondération basée sur le nombre de maisons, révélant les variations régionales.
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.pyplot(fig3)
            st.markdown(f"""
            <div style="background-color: {background_color}; padding: 10px; border: 1px solid {border_color}; color: white; margin-top: 10px;">
            Le scatter plot représente la relation entre le nombre de maisons à vendre et le prix moyen au m² par commune, coloré par département pour identifier les tendances. 1 point = 1 commune.
            </div>
            """, unsafe_allow_html=True)
        
    except FileNotFoundError:
        st.error("Les fichiers csv/STEP05/STEP05_all_bretagne.csv et/ou STEP07_map_densite.html n'ont pas été trouvés.")
    except Exception as e:
        st.error(f"Erreur lors du chargement des statistiques: {e}")

# Section d'estimation de prix par KNN
with st.expander("Estimation de prix par KNN"):
    st.write("Entrez les caractéristiques de la maison pour estimer son prix basé sur les maisons similaires dans la même commune.")
    # --- Charger les données pour KNN ---
    df_knn = load_knn_data()
    # --- Charger les codes INSEE ---
    df_insee = load_insee_codes()

    with st.form("knn_form"):
        col1, col2 = st.columns(2)
        with col1:
            ville = st.text_input("Nom de la commune", value="quimper")
            taille = st.text_input("Taille de la maison (m²)", value="120")
        with col2:
            terrain = st.text_input("Taille du terrain (m²) (optionnel)", value="150")
            pieces = st.text_input("Nombre de pièces (optionnel)", value="5")
        
        submitted = st.form_submit_button("Estimer le prix")
        
        if submitted:
            try:
                ville_input = ville.strip()
                code_insee_int = get_insee_code(ville_input, df_insee)
                taille_int = int(taille)
                terrain_int = int(terrain) if terrain.strip() else None
                pieces_int = int(pieces) if pieces.strip() else None
                prix, houses_data, num_maisons, _ = knn_estimation(df_knn, code_insee_int, taille_int, terrain_int, pieces_int, max_distance=30)
                if prix is not None:
                    st.success(f"Prix estimé : {prix:,.0f} €")
                    houses = houses_data
                    if len(houses) == 1:
                        st.write("Une maison très similaire trouvée. Le prix indiqué est le prix exact de cette maison. Attention il ne prend pas en compte d'autres facteurs comme l'état du bien, l'année de construction, la localisation précise dans la commune, etc.")
                    else:
                        st.write("Le prix est une moyenne des maisons similaires ci-dessous. Attention il ne prend pas en compte d'autres facteurs comme l'état du bien, l'année de construction, la localisation précise dans la commune, etc.")
                    if len(houses) == 1:
                        st.write("Maison très similaire :")
                    else:
                        st.write("Maisons les plus proches :")
                    div_html = """
                    <div style="margin-bottom:15px; text-align: center; border: 1px solid {border_color}; padding: 10px; margin: 5px; background-color: {background_color}; color: white;">
                    <h4>{nom}</h4>
                    <div style="display: flex; justify-content: space-around; margin-bottom: 10px;">
                    <div style="text-align: center; padding: 8px; margin: 4px; background-color: #0e1f32;">
                    <div style="font-weight: bold;">Lieu</div>
                    <div>{lieu}</div>
                    </div>
                    <div style="text-align: center; padding: 8px; margin: 4px; background-color: #0e1f32;">
                    <div style="font-weight: bold;">Pièces</div>
                    <div>{pieces}</div>
                    </div>
                    <div style="text-align: center; padding: 8px; margin: 4px; background-color: #0e1f32;">
                    <div style="font-weight: bold;">Taille</div>
                    <div>{taille} m²</div>
                    </div>
                    <div style="text-align: center; padding: 8px; margin: 4px; background-color: #0e1f32;">
                    <div style="font-weight: bold;">Terrain</div>
                    <div>{terrain} m²</div>
                    </div>
                    <div style="text-align: center; padding: 8px; margin: 4px; background-color: #0e1f32;">
                    <div style="font-weight: bold;">Prix</div>
                    <div>{prix:.0f} €</div>
                    </div>
                    </div>
                    <div style="margin-top: 10px;">
                    <a href="{lien}" target="_blank" style="background-color: {text_highlight_color}; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; display: inline-block;">Voir l'annonce</a>
                    </div>
                    </div>
                    """
                    if len(houses) > 0:
                        if len(houses) == 1:
                            cols = st.columns(1)
                            with cols[0]:
                                house = houses[0]
                                nom = house['Nom']
                                lieu = house['Lieu']
                                pieces_h = house['Pieces']
                                taille_h = house['Taille']
                                terrain_h = house['Taille_terrain']
                                prix_h = house['Prix']
                                lien = house['Lien']
                                pieces_str = f"{pieces_h}" if not pd.isna(pieces_h) else "N/A"
                                terrain_str = f"{terrain_h} m²" if not pd.isna(terrain_h) else "N/A"
                                st.markdown(div_html.format(nom=nom, lieu=lieu, pieces=pieces_str, taille=taille_h, terrain=terrain_str, prix=prix_h, lien=lien, border_color=border_color, background_color=background_color, text_highlight_color=text_highlight_color), unsafe_allow_html=True)
                        else:
                            col1, col2 = st.columns(2)
                            for i, house in enumerate(houses):
                                nom = house['Nom']
                                lieu = house['Lieu']
                                pieces_h = house['Pieces']
                                taille_h = house['Taille']
                                terrain_h = house['Taille_terrain']
                                prix_h = house['Prix']
                                lien = house['Lien']
                                pieces_str = f"{pieces_h}" if not pd.isna(pieces_h) else "N/A"
                                terrain_str = f"{terrain_h} m²" if not pd.isna(terrain_h) else "N/A"
                                if i % 2 == 0:
                                    with col1:
                                        st.markdown(div_html.format(nom=nom, lieu=lieu, pieces=pieces_str, taille=taille_h, terrain=terrain_str, prix=prix_h, lien=lien, border_color=border_color, background_color=background_color, text_highlight_color=text_highlight_color), unsafe_allow_html=True)
                                else:
                                    with col2:
                                        st.markdown(div_html.format(nom=nom, lieu=lieu, pieces=pieces_str, taille=taille_h, terrain=terrain_str, prix=prix_h, lien=lien, border_color=border_color, background_color=background_color, text_highlight_color=text_highlight_color), unsafe_allow_html=True)
                else:
                    st.error(houses_data)
            except ValueError:
                st.error("Veuillez entrer des valeurs numériques valides.")
