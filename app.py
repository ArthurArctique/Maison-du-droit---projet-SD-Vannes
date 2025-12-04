import dash
from dash import dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import random
import threading
import time
import requests 
import sqlite3
import json
import os
from datetime import datetime

# =============================================================================
# 1. LISTE DES VILLES (POUR LE GÉOCODAGE AUTOMATIQUE)
# =============================================================================
LISTE_VILLES_CIBLES = [
    "Allaire", "Ambon", "Arradon", "Arzal", "Arzon", "Augan", "Auray", "Baden", "Baud", "Béganne", "Beignon", 
    "Belle-Ile", "Belz", "Berné", "Berric", "Bieuzy", "Bignan", "Billers", "Billio", "Bohal", "Brandérion", 
    "Brandivy", "Brech", "Bréhan", "Brignac", "Bubry", "Buléon", "Caden", "Calan", "Camoël", "Camors", 
    "Campénéac", "Carentoir", "Carnac", "Caro", "Caudan", "Cléguérec", "Cléguers", "Colpo", "Concoret", 
    "Cournon", "Crac'h", "Crédin", "Croixanvec", "Cruguel", "Damgan", "Elven", "Erdeven", "Etel", "Evellys", 
    "Evriguet", "Férel", "Gavres", "Glénac", "Gestel", "Gourhel", "Gourrin", "Grand-Champ", "Guegon", 
    "Guéhenno", "Gueltas", "Guémené-sur-Scorff", "Guénin", "Guer", "Guern", "Guidel", "Guillac", "Guilliers", 
    "Guiscriff", "Helléan", "Hennebont", "Ile d'Arz", "Ile de Groix", "Ile de Hoedic", "Ile de Houat", 
    "Ile aux Moines", "Inguiniel", "Inzinzac-Lochrist", "Josselin", "Kerfourn", "Kergrist", "Kernascléden", 
    "Kervignac", "La Chapelle Caro", "La Chapelle Gaceline", "La Chapelle Neuve", "La Croix Helléan", 
    "La Gascilly", "La Grée-Saint-Laurent", "La Roche-Bernard", "La Trinité-Porhoët", "La Trinité-sur-Mer", 
    "La Trinité-Surzur", "La Vraie-Croix", "Landaul", "Landévant", "Lanester", "Langoëlan", "Langonnet", 
    "Languidic", "Lannouée", "Lantillac", "Lanvaudan", "Lanvénegen", "Larmor-Baden", "Larmor-Plage", "Larré", 
    "Lauzach", "Le Bono", "Le Cours", "Le Croisty", "Le Faouët", "Les Forges de Lannouée", "Les Fougerêts", 
    "Le Guerno", "Le Hézo", "Le Roc-Saint-André", "Le Saint", "Le Sourn", "Le Tour-du-Parc", "Lignol", 
    "Limerzel", "Lizio", "Locmalo", "Locmaria-Grand-Champ", "Locmariaquer", "Locminé", "Locmiquélic", 
    "Locoal-Mendon", "Locqueltas", "Lorient", "Loyat", "Malensac", "Malestroit", "Malguénac", "Marzan", 
    "Mauron", "Melrand", "Ménéac", "Merlevenez", "Meslan", "Meucon", "Missiriac", "Mohon", "Molac", 
    "Monteneuf", "Monterblanc", "Monterrein", "Montertelot", "Moréac", "Moustoir-Ac", "Moustoir-Remungol", 
    "Muzillac", "Naizin", "Néant-sur-Yvel", "Neuillac", "Nivillac", "Nostang", "Noyal-Muzillac", 
    "Noyal-Pontivy", "Péaule", "Peillac", "Penestin", "Persquen", "Plaudren", "Plescop", "Pleucadeuc", 
    "Pleugriffet", "Ploemel", "Ploemeur", "Ploërdut", "Ploeren", "Ploërmel", "Plouay", "Plougoumelen", 
    "Plouharnel", "Plouhinec", "Plouray", "Pluherlin", "Plumelec", "Pluméliau", "Plumelin", "Plumergat", 
    "Pluneret", "Pluvigner", "Pont-Scorff", "Pontivy", "Porcaro", "Port-Louis", "Priziac", "Quelneuc", 
    "Questembert", "Queven", "Quiberon", "Quily", "Quistinic", "Radenac", "Réguiny", "Réminiac", "Remungol", 
    "Riantec", "Rieux", "Rochefort-en-Terre", "Rohan", "Roudouallec", "Ruffiac", "Sarzeau", "Séglien", 
    "Séné", "Sérent", "Silfiac", "St-Abraham", "St-Aignan", "St-Allouestre", "St-Armel", "St-Avé", 
    "St-Barthélémy", "St-Brieuc de Mauron", "St-Caradec-Trégomel", "St-Congard", "St Connec", "St-Dolay", 
    "St-Gérand", "St-Gildas-de-Rhuys", "St-Gonnery", "St-Gorgon", "St-Gravé", "St-Guyomard", 
    "St-Jacut-les-Pins", "St-Jean-Brévelay", "St-Jean-la-Poterie", "St-Laurent-sur-Oust", "St-Léry", 
    "St-Malo-de-Beignon", "St-Malo-les-Trois-Fontaines", "St-Marcel", "St-Martin-sur-Oust", 
    "St-Nicolas-du-Tertre", "St-Nolff", "St-Perreux", "St-Philibert", "St-Pierre-Quiberon", "St-Servant", 
    "St-Thuriau", "St-Tugdual", "St-Vincent-sur-Oust", "Ste-Anne-d'Auray", "Ste-Brigitte", "Ste-Hélène", 
    "Sulniac", "Surzur", "Taupont", "Tréhillac", "Theix-Noyalo", "Tréal", "Trédion", "Treffléan", 
    "Tréhoranteuc", "Val d'Oust", "Vannes"
]

# =============================================================================
# 2. SYSTÈME GÉOCODAGE API
# =============================================================================
CACHE_FILE = "coords_cache.json"

def get_coords_from_api(ville):
    try:
        clean_ville = ville.split(" -")[0].split("(")[0].strip()
        url = f"https://api-adresse.data.gouv.fr/search/?q={clean_ville}&limit=1"
        response = requests.get(url, timeout=2)
        if response.status_code == 200 and response.json()['features']:
            coords = response.json()['features'][0]['geometry']['coordinates']
            return [coords[1], coords[0]]
    except: pass
    return None

def build_gps_dictionary(villes_list):
    coords_dict = {}
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as f: coords_dict = json.load(f)
    
    missing = [v for v in villes_list if v not in coords_dict]
    if missing:
        print(f"🌍 Géocodage API de {len(missing)} villes...")
        coords_dict["Vannes"] = [47.6582, -2.7608]
        for i, ville in enumerate(missing):
            gps = get_coords_from_api(ville)
            coords_dict[ville] = gps if gps else [47.6582, -2.7608]
            if i % 10 == 0: time.sleep(0.1)
        with open(CACHE_FILE, 'w', encoding='utf-8') as f: json.dump(coords_dict, f, ensure_ascii=False)
            
    return coords_dict

GPS_CACHE = build_gps_dictionary(LISTE_VILLES_CIBLES)

# =============================================================================
# 3. CHARGEMENT SQLITE (NOMS NATIFS)
# =============================================================================
def load_data_from_sqlite():
    db_filename = "base_donnees.db"
    print(f"Connexion SQL: {db_filename}...")
    
    try:
        conn = sqlite3.connect(db_filename)
        # On charge la table telle quelle
        query = "SELECT * FROM ENTRETIEN"
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            print("⚠️ Table ENTRETIEN vide.")
            return generate_fake_backup()

    except Exception as e:
        print(f"ERREUR SQL: {e}")
        return generate_fake_backup()

    # --- PAS DE RENOMMAGE (On utilise les noms SQL) ---
    # Colonnes attendues : DATE_ENT, SEXE, AGE, SIT_FAM, PROFESSION, VIENT_PR, MODE
    
    # --- NETTOYAGE & ENRICHISSEMENT ---
    
    # Dates (Basé sur DATE_ENT)
    if 'DATE_ENT' in df.columns:
        df['DATE_ENT'] = pd.to_datetime(df['DATE_ENT'], errors='coerce').fillna(datetime(2024, 1, 1))
        df['Annee'] = df['DATE_ENT'].dt.year.astype(str)
        df['Mois'] = df['DATE_ENT'].dt.strftime('%Y-%m')
        df['Trimestre'] = 'T' + ((df['DATE_ENT'].dt.month - 1) // 3 + 1).astype(str)
    else:
        # Création de données temporelles par défaut si DATE_ENT manque
        df['DATE_ENT'] = datetime(2024, 1, 1)
        df['Annee'] = "2024"
        df['Mois'] = "2024-01"
        df['Trimestre'] = "T1"

    # Age numérique
    if 'AGE' in df.columns:
        df['AGE'] = pd.to_numeric(df['AGE'], errors='coerce').fillna(0).astype(int)

    # --- GÉOCODAGE ---
    # On cherche une colonne ville/commune. Si absente, on met Vannes.
    col_ville = next((c for c in ['VILLE', 'COMMUNE', 'Domicile'] if c in df.columns), None)
    
    if col_ville:
        df['Ref_Ville'] = df[col_ville] # On normalise le nom pour le code
    else:
        df['Ref_Ville'] = "Vannes"

    def apply_gps(ville_nom, type_coord):
        v_clean = str(ville_nom).strip()
        coords = GPS_CACHE.get(v_clean)
        if not coords:
            # Recherche floue
            for k, val in GPS_CACHE.items():
                if k in v_clean: coords = val; break
        if not coords: coords = GPS_CACHE.get("Vannes", [47.6582, -2.7608])
        
        bruit = random.uniform(-0.005, 0.005)
        return coords[0] + bruit if type_coord == 'lat' else coords[1] + bruit

    df['Latitude'] = df['Ref_Ville'].apply(lambda x: apply_gps(x, 'lat'))
    df['Longitude'] = df['Ref_Ville'].apply(lambda x: apply_gps(x, 'lon'))

    return df.sort_values('DATE_ENT')

def generate_fake_backup():
    print("!!! MODE SECOURS !!!")
    return pd.DataFrame([{
        'SEXE':'Femme','AGE':30,'SIT_FAM':'Célibataire','PROFESSION':'Employé',
        'VIENT_PR':'Logement','MODE':'Téléphone','Ref_Ville':'Vannes',
        'DATE_ENT':datetime(2024,1,1),'Annee':'2024','Mois':'2024-01','Trimestre':'T1',
        'Latitude':47.65,'Longitude':-2.76
    }])

df_global = load_data_from_sqlite()

# =============================================================================
# 4. CONFIGURATION DASH
# =============================================================================
COLOR_NAVY = "#003366"
COLOR_GOLD = "#D4AF37"
COLOR_BG = "#F4F6F9"

def clean_layout(fig):
    fig.update_layout(plot_bgcolor=COLOR_BG, paper_bgcolor=COLOR_BG, font={'color': COLOR_NAVY}, margin=dict(t=40, l=10, r=10, b=10), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    return fig

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LUX], suppress_callback_exceptions=True)
app.title = "Reporting MDD"

sidebar = html.Div([
    html.Div([html.H3("MDD", style={'color': COLOR_GOLD, 'fontWeight': 'bold'}), html.H5("Vannes", style={'color': 'white'})], className="text-center mb-4 fade-in-left"),
    dbc.Nav([
        dbc.NavLink("📊 Tableau de Bord", href="/", active="exact", className="nav-link-custom"),
        dbc.NavLink("📋 Données", href="/data", active="exact", className="nav-link-custom"),
        dbc.NavLink("📥 Export PDF", href="/export", active="exact", className="nav-link-custom"),
    ], vertical=True, pills=True, className="mb-4 fade-in-left", style={'animationDelay': '0.1s'}),
    html.Div([
        html.H5("FILTRES", style={'color': COLOR_GOLD, 'fontWeight': 'bold', 'borderBottom': '1px solid white'}),
        html.Label("Année", style={'color': 'white', 'marginTop': '10px'}),
        dcc.Dropdown(id='filter-year', options=[{'label': 'Tout', 'value': 'ALL'}] + [{'label': str(y), 'value': str(y)} for y in sorted(df_global['Annee'].unique())], value='ALL', clearable=False, style={'borderRadius': '5px'}),
        html.Label("Période", style={'color': 'white', 'marginTop': '10px'}),
        dcc.Dropdown(id='filter-period', options=[{'label': 'Toute l\'année', 'value': 'ALL'}, {'label': 'T1', 'value': 'T1'}, {'label': 'T2', 'value': 'T2'}, {'label': 'T3', 'value': 'T3'}, {'label': 'T4', 'value': 'T4'}], value='ALL', style={'borderRadius': '5px'}),
        html.Label("Ville", style={'color': 'white', 'marginTop': '10px'}),
        dcc.Dropdown(id='filter-city', options=[{'label': 'Toutes', 'value': 'ALL'}] + [{'label': str(v), 'value': str(v)} for v in sorted(df_global['Ref_Ville'].astype(str).unique())], value='ALL', style={'borderRadius': '5px'}),
    ], className="filter-box fade-in-left", style={'animationDelay': '0.2s'})
], style={"position": "fixed", "top": 0, "left": 0, "bottom": 0, "width": "18rem", "padding": "2rem 1rem", "background-color": COLOR_NAVY, "color": "white", "display": "flex", "flexDirection": "column", "overflowY": "auto"}, className="no-print")

content = html.Div(id="page-content", style={"margin-left": "20rem", "padding": "2rem", "backgroundColor": COLOR_BG, "minHeight": "100vh"})

app.layout = html.Div([dcc.Location(id="url"), dcc.Store(id='client-view-index', data=0), dcc.Store(id='activity-view-index', data=0), dcc.Store(id='store-current-tab', data="btn-activite"), sidebar, content], id="main-container")

@app.callback(
    [Output("dashboard-content", "children"), Output("btn-activite", "color"), Output("btn-clients", "color"), Output("btn-carte", "color"), Output("btn-arrow-next", "style"), Output("btn-arrow-activity", "style"), Output("btn-arrow-activity", "children"), Output("btn-arrow-activity", "className"), Output("client-view-index", "data"), Output("activity-view-index", "data"), Output("store-current-tab", "data")],
    [Input("btn-activite", "n_clicks"), Input("btn-clients", "n_clicks"), Input("btn-carte", "n_clicks"), Input("btn-arrow-next", "n_clicks"), Input("btn-arrow-activity", "n_clicks"), Input("filter-year", "value"), Input("filter-period", "value"), Input("filter-city", "value")],
    [State("client-view-index", "data"), State("activity-view-index", "data"), State("store-current-tab", "data")]
)
def update_dashboard(b1, b2, b3, b_arr_cli, b_arr_act, f_year, f_period, f_city, cli_idx, act_idx, current_tab):
    
    # 1. FILTRAGE
    dff = df_global.copy()
    if f_year != 'ALL': dff = dff[dff['Annee'] == f_year]
    if f_period != 'ALL': dff = dff[dff['Trimestre'] == f_period]
    if f_city != 'ALL': dff = dff[dff['Ref_Ville'].astype(str) == f_city]

    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else "btn-activite"

    if "filter" in trigger_id: trigger_id = current_tab
    else:
        if trigger_id == "btn-arrow-next": cli_idx = (cli_idx + 1) % 2; trigger_id = "btn-clients"
        elif trigger_id == "btn-arrow-activity": act_idx = (act_idx + 1) % 2; trigger_id = "btn-activite"
        current_tab = trigger_id

    colors, arrow_cli, arrow_act = ["light", "light", "light"], {'display': 'none'}, {'display': 'none'}
    act_btn_txt, act_btn_cls = [html.Span("Voir l'évolution "), html.I(className="bi bi-graph-up")], "btn-suite ms-auto shadow-sm btn-anim"
    content = html.Div("Aucune donnée.", className="text-center mt-5 text-muted")

    if not dff.empty:
        # ACTIVITE (Utilisation de MODE et VIENT_PR)
        if trigger_id == "btn-activite":
            colors[0] = "primary"; arrow_act = {'display': 'inline-block'}
            if act_idx == 0:
                fig1 = px.bar(dff['MODE'].value_counts(), title="Modes de Contact", color_discrete_sequence=[COLOR_NAVY])
                fig2 = px.bar(dff['VIENT_PR'].value_counts(), title="Types de Demandes", orientation='h', color_discrete_sequence=[COLOR_GOLD])
                content = dbc.Row([dbc.Col(dcc.Graph(figure=clean_layout(fig1)), width=6), dbc.Col(dcc.Graph(figure=clean_layout(fig2)), width=6)])
            else:
                act_btn_txt = [html.I(className="bi bi-arrow-left me-2"), html.Span("Retour Synthèse")]; act_btn_cls = "btn-warning text-white ms-auto shadow-sm btn-anim"
                df_t = dff.groupby('Mois').size().reset_index(name='Nombre')
                fig = go.Figure()
                fig.add_trace(go.Bar(x=df_t['Mois'], y=df_t['Nombre'], name='Volume', marker_color=COLOR_NAVY, opacity=0.3))
                fig.add_trace(go.Scatter(x=df_t['Mois'], y=df_t['Nombre'], name='Tendance', mode='lines+markers', line=dict(color=COLOR_GOLD, width=3), fill='tozeroy', fillcolor='rgba(212, 175, 55, 0.2)'))
                content = dbc.Row([dbc.Col(dcc.Graph(figure=clean_layout(fig).update_layout(title="Évolution")), width=12)])
        
        # CLIENTS (Utilisation de AGE, SIT_FAM, PROFESSION, SEXE)
        elif trigger_id == "btn-clients":
            colors[1] = "primary"; arrow_cli = {'display': 'inline-block'}
            if cli_idx == 0:
                fig_a = px.histogram(dff, x="AGE", title="Âges", color_discrete_sequence=[COLOR_NAVY])
                fig_b = px.bar(dff['SIT_FAM'].value_counts(), title="Situation Familiale", color_discrete_sequence=[COLOR_GOLD])
            else:
                fig_a = px.pie(dff, names='PROFESSION', color_discrete_sequence=px.colors.sequential.Blues)
                fig_b = px.pie(dff, names='SEXE', title="H/F", hole=0.5, color_discrete_sequence=[COLOR_NAVY, COLOR_GOLD])
            content = dbc.Row([dbc.Col(dcc.Graph(figure=clean_layout(fig_a)), width=6), dbc.Col(dcc.Graph(figure=clean_layout(fig_b)), width=6)])
        
        # CARTE (Utilisation de VIENT_PR pour la couleur)
        elif trigger_id == "btn-carte":
            colors[2] = "primary"
            fig = px.scatter_mapbox(dff, lat="Latitude", lon="Longitude", size=[10]*len(dff), color="VIENT_PR", zoom=9, height=600, opacity=0.7)
            content = dbc.Row([dbc.Col(dcc.Graph(figure=fig.update_layout(mapbox_style="carto-positron", margin={"r":0,"t":0,"l":0,"b":0})), width=12)])

    return content, colors[0], colors[1], colors[2], arrow_cli, arrow_act, act_btn_txt, act_btn_cls, cli_idx, act_idx, current_tab

@app.callback([Output("page-content", "children")], [Input("url", "pathname"), Input("filter-year", "value"), Input("filter-period", "value"), Input("filter-city", "value")])
def render_main(path, fy, fp, fc):
    dff = df_global.copy()
    if fy != 'ALL': dff = dff[dff['Annee'] == fy]
    if fp != 'ALL': dff = dff[dff['Trimestre'] == fp]
    if fc != 'ALL': dff = dff[dff['Ref_Ville'].astype(str) == fc]
    
    nb, top, age = len(dff), dff['VIENT_PR'].mode()[0] if len(dff)>0 else "-", int(dff['AGE'].mean()) if len(dff)>0 else 0

    if path in ["/", "/dashboard"]:
        return [html.Div([
            dbc.Row([
                dbc.Col(dbc.Card([html.H2(str(nb), style={'color': COLOR_GOLD}), html.H6("Dossiers")], body=True, className="kpi-card shadow-sm text-center"), width=4),
                dbc.Col(dbc.Card([html.H2(str(top), style={'color': COLOR_NAVY, 'fontSize': '1.2rem'}), html.H6("Top Demande")], body=True, className="kpi-card shadow-sm text-center"), width=4),
                dbc.Col(dbc.Card([html.H2(f"{age} ans", style={'color': COLOR_NAVY}), html.H6("Age Moyen")], body=True, className="kpi-card shadow-sm text-center"), width=4)
            ], className="mb-4 fade-in-up"),
            html.Div([
                dbc.Button("Activité", id="btn-activite", className="me-2 btn-nav-custom btn-anim", color="primary"),
                dbc.Button("Clients", id="btn-clients", className="me-2 btn-nav-custom btn-anim", color="light"),
                dbc.Button("Carte", id="btn-carte", className="me-2 btn-nav-custom btn-anim", color="light"),
                dbc.Button([html.Span("Evol "), html.I(className="bi bi-graph-up")], id="btn-arrow-activity", className="btn-suite ms-auto shadow-sm btn-anim", style={'display': 'none'}),
                dbc.Button([html.Span("Suite "), html.I(className="bi bi-arrow-right")], id="btn-arrow-next", className="btn-suite ms-auto shadow-sm btn-anim", style={'display': 'none'})
            ], className="mb-4 d-flex align-items-center fade-in-up", style={'animationDelay': '0.1s'}),
            html.Div(id="dashboard-content", className="fade-in-up", style={'animationDelay': '0.2s'})
        ])]
    elif path == "/data":
        return [html.Div([html.H2("Données", style={'color': COLOR_NAVY}), html.Hr(style={'borderColor': COLOR_GOLD}), dash_table.DataTable(data=dff.to_dict('records'), columns=[{"name": i, "id": i} for i in dff.columns if i not in ['Latitude', 'Longitude']], page_size=15, style_header={'backgroundColor': COLOR_NAVY, 'color': 'white'}, filter_action="native", sort_action="native")], className="fade-in-up")]
    elif path == "/export":
        f1 = px.bar(dff['MODE'].value_counts(), title="Modes", color_discrete_sequence=[COLOR_NAVY])
        f2 = px.pie(dff, names='PROFESSION', color_discrete_sequence=px.colors.sequential.Blues)
        return [html.Div([html.Div([html.H2("PDF", style={'color': COLOR_NAVY}), html.Button("🖨️ Imprimer", id="btn-print", className="btn btn-lg btn-warning text-white mb-5")], className="text-center no-print"), html.Div([html.H1("Rapport", className="text-center mb-5"), dbc.Row([dbc.Col(dcc.Graph(figure=clean_layout(f1)), width=6), dbc.Col(dcc.Graph(figure=clean_layout(f2)), width=6)])], style={'backgroundColor': 'white', 'padding': '20px'})], className="fade-in-up")]

app.index_string = '''<!DOCTYPE html><html><head>{%metas%}<title>MDD Reporting</title>{%favicon%}{%css%}<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.5.0/font/bootstrap-icons.css"><style>.btn-primary { background-color: #003366 !important; border-color: #003366 !important; }.btn-warning { background-color: #D4AF37 !important; border-color: #D4AF37 !important; color: white !important;}.btn-suite { background-color: white; color: #D4AF37; border: 2px solid #D4AF37; border-radius: 50px; padding: 5px 20px; font-weight: bold; transition: all 0.3s ease; }.btn-anim:hover { transform: scale(1.05); box-shadow: 0 5px 15px rgba(0,0,0,0.2) !important; }.btn-suite:hover { background-color: #D4AF37; color: white; transform: scale(1.05); }.filter-box { background-color: #2C3E50; padding: 15px; border-radius: 10px; margin-top: auto; margin-bottom: 20px; }.nav-link-custom { color: rgba(255,255,255,0.8) !important; font-size: 1.1rem; margin-bottom: 10px; transition: 0.3s; }.nav-link-custom:hover { padding-left: 20px; color: white !important; }.nav-link-custom.active { background-color: #D4AF37 !important; color: white !important; font-weight: bold; }@keyframes slideInLeft { from { opacity: 0; transform: translateX(-50px); } to { opacity: 1; transform: translateX(0); } }.fade-in-left { animation: slideInLeft 0.8s ease-out forwards; }@keyframes fadeInUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }.fade-in-up { animation: fadeInUp 0.8s ease-out forwards; }@media print { .no-print { display: none !important; } #page-content { margin-left: 0 !important; width: 100%; padding: 0 !important; background-color: white !important;} }</style></head><body>{%app_entry%}<footer>{%config%}{%scripts%}{%renderer%}</footer></body></html>'''
app.clientside_callback("""function(n) { if (n > 0) { window.print(); } return ""; }""", Output("btn-print", "children"), Input("btn-print", "n_clicks"), prevent_initial_call=True)

if __name__ == '__main__':
    url = "http://127.0.0.1:8050/"
    def open_browser():
        print("Vérification serveur...")
        for i in range(40):
            try:
                if requests.get(url, timeout=0.2).status_code == 200:
                    import webbrowser; webbrowser.open(url); return
            except: time.sleep(0.5)
    threading.Thread(target=open_browser).start()
    app.run(debug=False)