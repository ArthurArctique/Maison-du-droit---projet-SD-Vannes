import dash
from dash import dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import random
import threading
import time
# import requests  # <--- COMMENTÉ
import sqlite3
# import json      # <--- COMMENTÉ
import os
from datetime import datetime

# =============================================================================
# 1. LISTE DES COMMUNES (POUR GÉOCODAGE) - COMMENTÉ
# =============================================================================
# LISTE_VILLES_CIBLES = [
#     "Allaire", "Ambon", "Arradon", "Arzal", "Arzon", "Augan", "Auray", "Baden", "Baud", "Béganne", "Beignon", 
#     ... (Liste masquée pour alléger) ...
#     "Tréhoranteuc", "Val d'Oust", "Vannes"
# ]

# =============================================================================
# 2. SYSTÈME DE GÉOCODAGE API - COMMENTÉ
# =============================================================================
# CACHE_FILE = "coords_cache.json"

# def get_coords_from_api(ville):
#     try:
#         clean_ville = ville.split(" -")[0].split("(")[0].strip()
#         url = f"https://api-adresse.data.gouv.fr/search/?q={clean_ville}&limit=1"
#         response = requests.get(url, timeout=2)
#         if response.status_code == 200:
#             data = response.json()
#             if data['features']:
#                 coords = data['features'][0]['geometry']['coordinates']
#                 return [coords[1], coords[0]] # Lat, Lon
#     except: pass
#     return None

# def build_gps_dictionary(villes_list):
#     coords_dict = {}
#     if os.path.exists(CACHE_FILE):
#         with open(CACHE_FILE, 'r', encoding='utf-8') as f: coords_dict = json.load(f)
    
#     missing = [v for v in villes_list if v not in coords_dict]
#     if missing:
#         print(f"🌍 Géocodage API de {len(missing)} villes...")
#         coords_dict["Vannes"] = [47.6582, -2.7608]
#         for i, ville in enumerate(missing):
#             gps = get_coords_from_api(ville)
#             coords_dict[ville] = gps if gps else [47.6582, -2.7608]
#             if i % 10 == 0: time.sleep(0.1)
#         with open(CACHE_FILE, 'w', encoding='utf-8') as f: json.dump(coords_dict, f, ensure_ascii=False)
            
#     return coords_dict

# GPS_CACHE = build_gps_dictionary(LISTE_VILLES_CIBLES) # <--- DÉSACTIVÉ

# =============================================================================
# 3. CHARGEMENT SQLITE (STRICT)
# =============================================================================
def load_data_from_sqlite():
    db_names = ["database.db", "../database.db", "base_donnees.db"]
    db_filename = None
    
    for name in db_names:
        if os.path.exists(name):
            db_filename = name
            break
            
    if not db_filename:
        print("❌ ERREUR CRITIQUE : Aucun fichier de base de données trouvé !")
        return pd.DataFrame()

    print(f"✅ Connexion SQL : {db_filename}")
    
    try:
        conn = sqlite3.connect(db_filename)
        query = "SELECT * FROM ENTRETIEN"
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            print("⚠️ Table ENTRETIEN vide.")
            return pd.DataFrame()

    except Exception as e:
        print(f"❌ ERREUR SQL CRITIQUE : {e}")
        return pd.DataFrame()

    # --- MAPPING SQL -> NOMS EXCEL ---
    mapping = {
        'DATE_ENT': 'Date',
        'SEXE': 'Sexe',
        'AGE': 'Age',
        'SIT_FAM': 'Situation',
        'PROFESSION': 'Profession',
        'VIENT_PR': 'Demande_Type',
        'MODE': 'Mode_Contact',
        'VILLE': 'Ville',
        'COMMUNE': 'Ville',
        'DOMICILE': 'Ville'
    }
    df = df.rename(columns=mapping)

    # --- NETTOYAGE ---
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['Annee'] = df['Date'].dt.year.astype(str).str.replace(r'\.0', '', regex=True)
        df['Mois'] = df['Date'].dt.strftime('%Y-%m')
        df['Trimestre'] = 'T' + ((df['Date'].dt.month - 1) // 3 + 1).astype(str)
    else:
        df['Date'] = pd.NaT
        df['Annee'] = "Inconnue"
        df['Mois'] = "Inconnu"
        df['Trimestre'] = "Inconnu"

    if 'Age' in df.columns:
        df['Age'] = pd.to_numeric(df['Age'], errors='coerce').fillna(0).astype(int)

    # --- GÉOCODAGE (COMMENTÉ) ---
    if 'Ville' not in df.columns:
        df['Ville'] = "Vannes" 

    # def apply_gps(ville_nom, type_coord):
    #     v_clean = str(ville_nom).strip()
    #     coords = GPS_CACHE.get(v_clean)
    #     if not coords:
    #         for k, val in GPS_CACHE.items():
    #             if k in v_clean: coords = val; break
    #     if not coords: coords = GPS_CACHE.get("Vannes", [47.6582, -2.7608])
        
    #     bruit = random.uniform(-0.005, 0.005)
    #     return coords[0] + bruit if type_coord == 'lat' else coords[1] + bruit

    # df['Latitude'] = df['Ville'].apply(lambda x: apply_gps(x, 'lat'))
    # df['Longitude'] = df['Ville'].apply(lambda x: apply_gps(x, 'lon'))

    return df.sort_values('Date')

# CHARGEMENT
df_global = load_data_from_sqlite()

if df_global.empty:
    print("⚠️ DÉMARRAGE AVEC DONNÉES VIDES.")

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

options_annee = sorted([x for x in df_global['Annee'].unique() if x != 'nan']) if not df_global.empty and 'Annee' in df_global.columns else []
options_ville = sorted([x for x in df_global['Ville'].astype(str).unique()]) if not df_global.empty and 'Ville' in df_global.columns else []

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
        dcc.Dropdown(id='filter-year', options=[{'label': 'Tout', 'value': 'ALL'}] + [{'label': str(y), 'value': str(y)} for y in options_annee], value='ALL', clearable=False, style={'borderRadius': '5px'}),
        html.Label("Période", style={'color': 'white', 'marginTop': '10px'}),
        dcc.Dropdown(id='filter-period', options=[{'label': 'Toute l\'année', 'value': 'ALL'}, {'label': 'T1', 'value': 'T1'}, {'label': 'T2', 'value': 'T2'}, {'label': 'T3', 'value': 'T3'}, {'label': 'T4', 'value': 'T4'}], value='ALL', style={'borderRadius': '5px'}),
        html.Label("Ville", style={'color': 'white', 'marginTop': '10px'}),
        dcc.Dropdown(id='filter-city', options=[{'label': 'Toutes', 'value': 'ALL'}] + [{'label': str(v), 'value': str(v)} for v in options_ville], value='ALL', style={'borderRadius': '5px'}),
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
    if df_global.empty:
        return html.Div("⚠️ Base de données vide ou introuvable.", className="text-center mt-5 text-danger"), "light", "light", "light", {'display': 'none'}, {'display': 'none'}, "", "", 0, 0, current_tab

    dff = df_global.copy()
    if f_year != 'ALL': dff = dff[dff['Annee'] == f_year]
    if f_period != 'ALL': dff = dff[dff['Trimestre'] == f_period]
    if f_city != 'ALL': dff = dff[dff['Ville'].astype(str) == f_city]

    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else "btn-activite"
    if "filter" in trigger_id: trigger_id = current_tab
    else:
        if trigger_id == "btn-arrow-next": cli_idx = (cli_idx + 1) % 2; trigger_id = "btn-clients"
        elif trigger_id == "btn-arrow-activity": act_idx = (act_idx + 1) % 2; trigger_id = "btn-activite"
        current_tab = trigger_id

    colors, arrow_cli, arrow_act = ["light", "light", "light"], {'display': 'none'}, {'display': 'none'}
    act_btn_txt, act_btn_cls = [html.Span("Voir l'évolution "), html.I(className="bi bi-graph-up")], "btn-suite ms-auto shadow-sm btn-anim"
    content = html.Div("Aucune donnée pour ces filtres.", className="text-center mt-5 text-muted")

    if not dff.empty:
        if trigger_id == "btn-activite":
            colors[0] = "primary"; arrow_act = {'display': 'inline-block'}
            if act_idx == 0:
                fig1 = px.bar(dff['Mode_Contact'].value_counts(), title="Modes de Contact", color_discrete_sequence=[COLOR_NAVY])
                fig2 = px.bar(dff['Demande_Type'].value_counts(), title="Types de Demandes", orientation='h', color_discrete_sequence=[COLOR_GOLD])
                content = dbc.Row([dbc.Col(dcc.Graph(figure=clean_layout(fig1)), width=6), dbc.Col(dcc.Graph(figure=clean_layout(fig2)), width=6)])
            else:
                act_btn_txt = [html.I(className="bi bi-arrow-left me-2"), html.Span("Retour Synthèse")]; act_btn_cls = "btn-warning text-white ms-auto shadow-sm btn-anim"
                df_t = dff.groupby('Mois').size().reset_index(name='Nombre')
                fig = go.Figure()
                fig.add_trace(go.Bar(x=df_t['Mois'], y=df_t['Nombre'], name='Volume', marker_color=COLOR_NAVY, opacity=0.3))
                fig.add_trace(go.Scatter(x=df_t['Mois'], y=df_t['Nombre'], name='Tendance', mode='lines+markers', line=dict(color=COLOR_GOLD, width=3), fill='tozeroy', fillcolor='rgba(212, 175, 55, 0.2)'))
                content = dbc.Row([dbc.Col(dcc.Graph(figure=clean_layout(fig).update_layout(title="Évolution Mensuelle")), width=12)])
        elif trigger_id == "btn-clients":
            colors[1] = "primary"; arrow_cli = {'display': 'inline-block'}
            if cli_idx == 0:
                fig_a = px.histogram(dff, x="Age", title="Âges", color_discrete_sequence=[COLOR_NAVY])
                fig_b = px.bar(dff['Situation'].value_counts(), title="Situation Familiale", color_discrete_sequence=[COLOR_GOLD])
            else:
                fig_a = px.pie(dff, names='Profession', color_discrete_sequence=px.colors.sequential.Blues)
                fig_b = px.pie(dff, names='Sexe', title="H/F", hole=0.5, color_discrete_sequence=[COLOR_NAVY, COLOR_GOLD])
            content = dbc.Row([dbc.Col(dcc.Graph(figure=clean_layout(fig_a)), width=6), dbc.Col(dcc.Graph(figure=clean_layout(fig_b)), width=6)])
        elif trigger_id == "btn-carte":
            colors[2] = "primary"
            # PARTIE CARTE DÉSACTIVÉE / COMMENTÉE
            content = html.Div("🗺️ La fonctionnalité Carte est désactivée temporairement.", className="text-center mt-5 text-muted")
            
            # Si tu veux réactiver, décommente ci-dessous et assure-toi que Latitude/Longitude existent
            # fig = px.scatter_mapbox(dff, lat="Latitude", lon="Longitude", size=[10]*len(dff), color="Demande_Type", zoom=9, height=600, opacity=0.7)
            # content = dbc.Row([dbc.Col(dcc.Graph(figure=fig.update_layout(mapbox_style="carto-positron", margin={"r":0,"t":0,"l":0,"b":0})), width=12)])

    return content, colors[0], colors[1], colors[2], arrow_cli, arrow_act, act_btn_txt, act_btn_cls, cli_idx, act_idx, current_tab

@app.callback([Output("page-content", "children")], [Input("url", "pathname"), Input("filter-year", "value"), Input("filter-period", "value"), Input("filter-city", "value")])
def render_main(path, fy, fp, fc):
    if df_global.empty: return [html.Div("⚠️ Base de données vide ou introuvable.", className="text-center mt-5 text-danger")]

    dff = df_global.copy()
    if fy != 'ALL': dff = dff[dff['Annee'] == fy]
    if fp != 'ALL': dff = dff[dff['Trimestre'] == fp]
    if fc != 'ALL': dff = dff[dff['Ville'].astype(str) == fc]
    
    nb, top, age = len(dff), dff['Demande_Type'].mode()[0] if len(dff)>0 else "-", int(dff['Age'].mean()) if len(dff)>0 else 0

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
                # BOUTON CARTE DÉSACTIVÉ OU NON-CLIQUABLE
                dbc.Button("Carte (OFF)", id="btn-carte", className="me-2 btn-nav-custom btn-anim", color="secondary", disabled=True),
                
                dbc.Button([html.Span("Evol "), html.I(className="bi bi-graph-up")], id="btn-arrow-activity", className="btn-suite ms-auto shadow-sm btn-anim", style={'display': 'none'}),
                dbc.Button([html.Span("Suite "), html.I(className="bi bi-arrow-right")], id="btn-arrow-next", className="btn-suite ms-auto shadow-sm btn-anim", style={'display': 'none'})
            ], className="mb-4 d-flex align-items-center fade-in-up", style={'animationDelay': '0.1s'}),
            html.Div(id="dashboard-content", className="fade-in-up", style={'animationDelay': '0.2s'})
        ])]
    elif path == "/data":
        return [html.Div([html.H2("Données", style={'color': COLOR_NAVY}), html.Hr(style={'borderColor': COLOR_GOLD}), dash_table.DataTable(data=dff.to_dict('records'), columns=[{"name": i, "id": i} for i in dff.columns if i not in ['Latitude', 'Longitude']], page_size=15, style_header={'backgroundColor': COLOR_NAVY, 'color': 'white'}, filter_action="native", sort_action="native")], className="fade-in-up")]
    elif path == "/export":
        f1 = px.bar(dff['Mode_Contact'].value_counts(), title="Modes", color_discrete_sequence=[COLOR_NAVY])
        f2 = px.pie(dff, names='Profession', color_discrete_sequence=px.colors.sequential.Blues)
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
        print("Serveur lent.")
    threading.Thread(target=open_browser).start()
    app.run(debug=False)