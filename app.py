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
import sqlite3 # Nouvelle librairie pour parler à la base de données
from datetime import datetime

# =============================================================================
# 1. CHARGEMENT DES DONNÉES DEPUIS SQLITE
# =============================================================================
def load_data_from_sqlite():
    db_filename = "base_donnees.db" # <--- NOM DU FICHIER DE TON COLLÈGUE
    print(f"Connexion à la base {db_filename}...")
    
    try:
        # Connexion à la base
        conn = sqlite3.connect(db_filename)
        
        # Requete SQL simple pour tout récupérer
        query = "SELECT * FROM ENTRETIEN"
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            print("ATTENTION : La table ENTRETIEN est vide.")
            return generate_fake_backup()

    except Exception as e:
        print(f"ERREUR SQLITE : {e}")
        print("Passage en mode secours (données fictives)...")
        return generate_fake_backup()

    # --- TRADUCTION DES CODES (TINYINT -> TEXTE) ---
    # C'est ici qu'on transforme les 1, 2, 3 en vrai texte pour les graphiques.
    # Demande à ton collègue les correspondances exactes !
    
    # Exemple de dictionnaire (A ADAPTER)
    map_sexe = {1: 'Femme', 2: 'Homme', 3: 'Autre'}
    map_mode = {1: 'Téléphone', 2: 'Physique', 3: 'Email', 4: 'Courrier'}
    map_prof = {1: 'Sans emploi', 2: 'Ouvrier', 3: 'Employé', 4: 'Cadre', 5: 'Retraité', 6: 'Etudiant'}
    map_vient_pr = {1: 'Famille', 2: 'Logement', 3: 'Travail', 4: 'Consommation', 5: 'Pénal', 6: 'Etrangers'}
    
    # Application des traductions (si la colonne existe)
    if 'SEXE' in df.columns: df['SEXE'] = df['SEXE'].map(map_sexe).fillna('Inconnu')
    if 'MODE' in df.columns: df['MODE'] = df['MODE'].map(map_mode).fillna('Autre')
    if 'PROFESSION' in df.columns: df['PROFESSION'] = df['PROFESSION'].map(map_prof).fillna('Autre')
    if 'VIENT_PR' in df.columns: df['VIENT_PR'] = df['VIENT_PR'].map(map_vient_pr).fillna('Divers')

    # --- MAPPING COLONNES SQL -> APP ---
    # On renomme les colonnes de la BDD pour qu'elles collent à mon code Dash
    mapping = {
        'DATE_ENT': 'Date',
        'SEXE': 'Sexe',
        'AGE': 'Age',
        'SIT_FAM': 'Situation',
        'PROFESSION': 'Profession',
        'VIENT_PR': 'Demande_Type',
        'MODE': 'Mode_Contact',
        # Pas de ville dans ta table SQL ? On va gérer ça plus bas.
    }
    df = df.rename(columns=mapping)

    # --- GESTION DATE ---
    # On s'assure que c'est bien une date
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    # Si date invalide ou vide, on met 2024 par défaut
    df['Date'] = df['Date'].fillna(datetime(2024, 1, 1))

    # Création des colonnes temporelles pour les filtres
    df['Annee'] = df['Date'].dt.year.astype(str)
    df['Mois'] = df['Date'].dt.strftime('%Y-%m')
    df['Trimestre'] = 'T' + ((df['Date'].dt.month - 1) // 3 + 1).astype(str)

    # --- GESTION GPS (CARTE) ---
    # Comme la table ENTRETIEN n'a pas de Ville, on met "Vannes" par défaut
    # pour que la carte affiche au moins quelque chose.
    coords_villes = {
        "Vannes": [47.6582, -2.7608],
        # Ajoute d'autres villes si tu récupères l'info plus tard
    }

    def get_gps(row):
        # Si tu as une colonne ville plus tard, remplace "Vannes" par row['Ville']
        ville_nom = "Vannes" 
        base = coords_villes.get("Vannes")
        
        # Petit décalage aléatoire pour éviter que les points s'empilent
        bruit_lat = random.uniform(-0.01, 0.01)
        bruit_lon = random.uniform(-0.01, 0.01)
        return pd.Series([base[0] + bruit_lat, base[1] + bruit_lon])

    df[['Latitude', 'Longitude']] = df.apply(get_gps, axis=1)
    # On crée une colonne Ville fictive pour le filtre si elle manque
    if 'Ville' not in df.columns:
        df['Ville'] = "Vannes (Par défaut)"

    return df.sort_values('Date')

# Fonction de secours (Si pas de BDD)
def generate_fake_backup():
    print("!!! MODE SECOURS : DONNÉES FICTIVES !!!")
    data = []
    for i in range(100):
        data.append({
            'Sexe': random.choice(['Femme', 'Homme']), 'Age': random.randint(20,80), 
            'Situation': 'Célibataire', 'Profession': 'Employé', 
            'Demande_Type': 'Logement', 'Mode_Contact': 'Physique', 'Ville': 'Vannes', 
            'Date': datetime(2024,1,1), 'Annee': '2024', 'Mois': '2024-01', 'Trimestre': 'T1',
            'Latitude': 47.65 + random.uniform(-0.01,0.01), 
            'Longitude': -2.76 + random.uniform(-0.01,0.01)
        })
    return pd.DataFrame(data)

# CHARGEMENT GLOBAL
df_global = load_data_from_sqlite()

# =============================================================================
# 2. DESIGN & CONFIGURATION
# =============================================================================
COLOR_NAVY = "#003366"
COLOR_GOLD = "#D4AF37"
COLOR_BG = "#F4F6F9"

def clean_layout(fig):
    fig.update_layout(
        plot_bgcolor=COLOR_BG, paper_bgcolor=COLOR_BG,
        font={'color': COLOR_NAVY},
        margin=dict(t=40, l=10, r=10, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LUX], suppress_callback_exceptions=True)
app.title = "Reporting MDD"

# =============================================================================
# 3. STRUCTURE (LAYOUT)
# =============================================================================

sidebar = html.Div(
    [
        html.Div([
            html.H3("MDD", style={'color': COLOR_GOLD, 'fontWeight': 'bold'}),
            html.H5("Vannes", style={'color': 'white'})
        ], className="text-center mb-4 fade-in-left"),
        
        dbc.Nav(
            [
                dbc.NavLink("📊 Tableau de Bord", href="/", active="exact", className="nav-link-custom"),
                dbc.NavLink("📋 Données", href="/data", active="exact", className="nav-link-custom"),
                dbc.NavLink("📥 Export PDF", href="/export", active="exact", className="nav-link-custom"),
            ],
            vertical=True, pills=True, className="mb-4 fade-in-left", style={'animationDelay': '0.1s'}
        ),

        # FILTRES DYNAMIQUES
        html.Div([
            html.H5("FILTRES", style={'color': COLOR_GOLD, 'fontWeight': 'bold', 'borderBottom': '1px solid white'}),
            
            html.Label("Année", style={'color': 'white', 'marginTop': '10px'}),
            dcc.Dropdown(
                id='filter-year',
                options=[{'label': 'Tout', 'value': 'ALL'}] + [{'label': str(y), 'value': str(y)} for y in sorted(df_global['Annee'].unique())],
                value='ALL', clearable=False, style={'borderRadius': '5px'}
            ),

            html.Label("Période", style={'color': 'white', 'marginTop': '10px'}),
            dcc.Dropdown(
                id='filter-period',
                options=[{'label': 'Toute l\'année', 'value': 'ALL'}, 
                         {'label': '1er Trimestre', 'value': 'T1'}, 
                         {'label': '2e Trimestre', 'value': 'T2'},
                         {'label': '3e Trimestre', 'value': 'T3'},
                         {'label': '4e Trimestre', 'value': 'T4'}],
                value='ALL', style={'borderRadius': '5px'}
            ),

            html.Label("Ville", style={'color': 'white', 'marginTop': '10px'}),
            dcc.Dropdown(
                id='filter-city',
                # .astype(str) corrige l'erreur de tri Texte/Nombre
                options=[{'label': 'Toutes', 'value': 'ALL'}] + [{'label': str(v), 'value': str(v)} for v in sorted(df_global['Ville'].astype(str).unique())],
                value='ALL', style={'borderRadius': '5px'}
            ),

        ], className="filter-box fade-in-left", style={'animationDelay': '0.2s'})
    ],
    style={"position": "fixed", "top": 0, "left": 0, "bottom": 0, "width": "18rem", "padding": "2rem 1rem", "background-color": COLOR_NAVY, "color": "white", "display": "flex", "flexDirection": "column", "overflowY": "auto"},
    className="no-print"
)

content = html.Div(id="page-content", style={"margin-left": "20rem", "padding": "2rem", "backgroundColor": COLOR_BG, "minHeight": "100vh"})

app.layout = html.Div([
    dcc.Location(id="url"), 
    dcc.Store(id='client-view-index', data=0),
    dcc.Store(id='activity-view-index', data=0),
    dcc.Store(id='store-current-tab', data="btn-activite"), 
    sidebar, 
    content
], id="main-container")

# =============================================================================
# 4. LOGIQUE (CALLBACKS)
# =============================================================================

@app.callback(
    [Output("dashboard-content", "children"),
     Output("btn-activite", "color"),
     Output("btn-clients", "color"),
     Output("btn-carte", "color"),
     Output("btn-arrow-next", "style"),
     Output("btn-arrow-activity", "style"), 
     Output("btn-arrow-activity", "children"),
     Output("btn-arrow-activity", "className"),
     Output("client-view-index", "data"),
     Output("activity-view-index", "data"),
     Output("store-current-tab", "data")],
    [Input("btn-activite", "n_clicks"),
     Input("btn-clients", "n_clicks"),
     Input("btn-carte", "n_clicks"),
     Input("btn-arrow-next", "n_clicks"),
     Input("btn-arrow-activity", "n_clicks"),
     Input("filter-year", "value"),
     Input("filter-period", "value"),
     Input("filter-city", "value")],
    [State("client-view-index", "data"),
     State("activity-view-index", "data"),
     State("store-current-tab", "data")]
)
def update_dashboard(b1, b2, b3, b_arr_cli, b_arr_act, f_year, f_period, f_city, cli_idx, act_idx, current_tab):
    
    # 1. FILTRAGE
    dff = df_global.copy()
    if f_year != 'ALL': dff = dff[dff['Annee'] == f_year]
    if f_period != 'ALL': dff = dff[dff['Trimestre'] == f_period]
    if f_city != 'ALL': dff = dff[dff['Ville'].astype(str) == f_city]

    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else "btn-activite"

    # 2. NAVIGATION INTELLIGENTE
    if "filter" in trigger_id:
        trigger_id = current_tab
    else:
        if trigger_id == "btn-arrow-next":
            cli_idx = (cli_idx + 1) % 2
            trigger_id = "btn-clients"
        elif trigger_id == "btn-arrow-activity":
            act_idx = (act_idx + 1) % 2
            trigger_id = "btn-activite"
        current_tab = trigger_id

    # Styles par défaut
    colors = ["light", "light", "light"]
    arrow_cli_style = {'display': 'none'}
    arrow_act_style = {'display': 'none'}
    act_btn_content = [html.Span("Voir l'évolution "), html.I(className="bi bi-graph-up")]
    act_btn_class = "btn-suite ms-auto shadow-sm btn-anim"
    
    content = html.Div("Aucune donnée disponible pour ces filtres.", className="text-center mt-5 text-muted")

    if not dff.empty:
        # --- ONGLET ACTIVITÉ ---
        if trigger_id == "btn-activite":
            colors[0] = "primary"
            arrow_act_style = {'display': 'inline-block'}
            
            if act_idx == 0:
                # Vue Barres
                fig1 = px.bar(dff['Mode_Contact'].value_counts(), title="Modes de Contact", color_discrete_sequence=[COLOR_NAVY])
                fig2 = px.bar(dff['Demande_Type'].value_counts(), title="Types de Demandes", orientation='h', color_discrete_sequence=[COLOR_GOLD])
                content = dbc.Row([dbc.Col(dcc.Graph(figure=clean_layout(fig1)), width=6), dbc.Col(dcc.Graph(figure=clean_layout(fig2)), width=6)])
            else:
                # Vue Courbe Evolution
                act_btn_content = [html.I(className="bi bi-arrow-left me-2"), html.Span("Retour Synthèse")]
                act_btn_class = "btn-warning text-white ms-auto shadow-sm btn-anim"
                
                df_time = dff.groupby('Mois').size().reset_index(name='Nombre')
                fig_combo = go.Figure()
                fig_combo.add_trace(go.Bar(x=df_time['Mois'], y=df_time['Nombre'], name='Volume', marker_color=COLOR_NAVY, opacity=0.3))
                fig_combo.add_trace(go.Scatter(x=df_time['Mois'], y=df_time['Nombre'], name='Tendance', mode='lines+markers', line=dict(color=COLOR_GOLD, width=3), fill='tozeroy', fillcolor='rgba(212, 175, 55, 0.2)'))
                clean_layout(fig_combo)
                fig_combo.update_layout(title="Évolution mensuelle des dossiers", showlegend=True)
                content = dbc.Row([dbc.Col(dcc.Graph(figure=fig_combo), width=12)])

        # --- ONGLET CLIENTS ---
        elif trigger_id == "btn-clients":
            colors[1] = "primary"
            arrow_cli_style = {'display': 'inline-block'}
            
            if cli_idx == 0:
                fig_a = px.histogram(dff, x="Age", title="Pyramide des Âges", color_discrete_sequence=[COLOR_NAVY])
                fig_b = px.bar(dff['Situation'].value_counts(), title="Situation Familiale", color_discrete_sequence=[COLOR_GOLD])
            else:
                fig_a = px.pie(dff, names='Profession', title="Catégorie Socio-Pro", color_discrete_sequence=px.colors.sequential.Blues)
                fig_a.update_traces(textposition='inside', textinfo='percent+label')
                fig_b = px.pie(dff, names='Sexe', title="Répartition H/F", hole=0.5, color_discrete_sequence=[COLOR_NAVY, COLOR_GOLD])
                fig_b.update_traces(textposition='inside', textinfo='percent+label')
            content = dbc.Row([dbc.Col(dcc.Graph(figure=clean_layout(fig_a)), width=6), dbc.Col(dcc.Graph(figure=clean_layout(fig_b)), width=6)])

        # --- ONGLET CARTE ---
        elif trigger_id == "btn-carte":
            colors[2] = "primary"
            # Carte Zoomable (Points fictifs autour de Vannes car pas de Ville dans SQL)
            fig_map = px.scatter_mapbox(
                dff, lat="Latitude", lon="Longitude", 
                size=[10]*len(dff), color="Demande_Type", 
                zoom=10, height=600, title="Répartition Géographique (Estimée)", opacity=0.7
            )
            fig_map.update_layout(mapbox_style="carto-positron", margin={"r":0,"t":0,"l":0,"b":0})
            content = dbc.Row([dbc.Col(dcc.Graph(figure=fig_map, config={'scrollZoom': True}), width=12)])

    return content, colors[0], colors[1], colors[2], arrow_cli_style, arrow_act_style, act_btn_content, act_btn_class, cli_idx, act_idx, current_tab

# Rendu de la page principale (KPIs + Nav)
@app.callback(
    [Output("page-content", "children")],
    [Input("url", "pathname"), Input("filter-year", "value"), Input("filter-period", "value"), Input("filter-city", "value")]
)
def render_main(pathname, f_year, f_period, f_city):
    
    dff = df_global.copy()
    if f_year != 'ALL': dff = dff[dff['Annee'] == f_year]
    if f_period != 'ALL': dff = dff[dff['Trimestre'] == f_period]
    if f_city != 'ALL': dff = dff[dff['Ville'].astype(str) == f_city]

    nb_total = len(dff)
    top_dem = dff['Demande_Type'].mode()[0] if nb_total > 0 else "-"
    try: age_moy = int(dff['Age'].mean())
    except: age_moy = 0

    if pathname == "/" or pathname == "/dashboard":
        return [html.Div([
            # KPI
            dbc.Row([
                dbc.Col(dbc.Card([html.H2(str(nb_total), style={'color': COLOR_GOLD, 'fontWeight': 'bold'}), html.H6("Dossiers Filtrés", className="text-muted")], body=True, className="kpi-card shadow-sm border-0 text-center"), width=4),
                dbc.Col(dbc.Card([html.H2(str(top_dem), style={'color': COLOR_NAVY, 'fontWeight': 'bold', 'fontSize': '1.3rem'}), html.H6("Top Demande", className="text-muted")], body=True, className="kpi-card shadow-sm border-0 text-center"), width=4),
                dbc.Col(dbc.Card([html.H2(f"{age_moy} ans", style={'color': COLOR_NAVY, 'fontWeight': 'bold'}), html.H6("Âge Moyen", className="text-muted")], body=True, className="kpi-card shadow-sm border-0 text-center"), width=4),
            ], className="mb-4 fade-in-up"),
            
            # Navigation
            html.Div([
                dbc.Button("Activité", id="btn-activite", n_clicks=0, className="me-2 btn-nav-custom btn-anim", color="primary"),
                dbc.Button("Clients", id="btn-clients", n_clicks=0, className="me-2 btn-nav-custom btn-anim", color="light"),
                dbc.Button("Carte", id="btn-carte", n_clicks=0, className="me-2 btn-nav-custom btn-anim", color="light"),
                dbc.Button([html.Span("Voir l'évolution "), html.I(className="bi bi-graph-up")], id="btn-arrow-activity", n_clicks=0, className="btn-suite ms-auto shadow-sm btn-anim", style={'display': 'none'}),
                dbc.Button([html.Span("Voir la suite "), html.I(className="bi bi-arrow-right")], id="btn-arrow-next", n_clicks=0, className="btn-suite ms-auto shadow-sm btn-anim", style={'display': 'none'})
            ], className="mb-4 d-flex align-items-center fade-in-up", style={'animationDelay': '0.1s'}),
            
            html.Div(id="dashboard-content", className="fade-in-up", style={'animationDelay': '0.2s'})
        ])]
    elif pathname == "/data":
        return [html.Div([
            html.H2("Données Filtrées", style={'color': COLOR_NAVY}),
            html.Hr(style={'borderColor': COLOR_GOLD}),
            dash_table.DataTable(data=dff.to_dict('records'), columns=[{"name": i, "id": i} for i in dff.columns if i not in ['Latitude', 'Longitude']], page_size=15, style_header={'backgroundColor': COLOR_NAVY, 'color': 'white'}, style_cell={'padding': '10px'}, filter_action="native", sort_action="native")
        ], className="fade-in-up")]
    elif pathname == "/export":
        fig1 = px.bar(dff['Mode_Contact'].value_counts(), title="Modes", color_discrete_sequence=[COLOR_NAVY])
        clean_layout(fig1)
        fig2 = px.pie(dff, names='Profession', color_discrete_sequence=px.colors.sequential.Blues)
        clean_layout(fig2)
        return [html.Div([
            html.Div([html.H2("Export PDF", style={'color': COLOR_NAVY}), html.Button("🖨️ Imprimer", id="btn-print", className="btn btn-lg btn-warning text-white mb-5 btn-anim")], className="text-center no-print fade-in-up"),
            html.Div([html.H1("Rapport MDD", className="text-center mb-5", style={'color': COLOR_NAVY}), dbc.Row([dbc.Col(html.Div([html.H3(str(nb_total)), html.P("Dossiers")]), className="text-center border p-3"), dbc.Col(html.Div([html.H3(str(top_dem)), html.P("Top Demande")]), className="text-center border p-3")], className="mb-5"), dbc.Row([dbc.Col(dcc.Graph(figure=clean_layout(fig1)), width=6), dbc.Col(dcc.Graph(figure=clean_layout(fig2)), width=6)])], style={'backgroundColor': 'white', 'padding': '20px'}, className="fade-in-up")
        ])]

# --- STYLES ET LANCEMENT ---
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}<title>MDD Reporting</title>{%favicon%}{%css%}
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.5.0/font/bootstrap-icons.css">
        <style>
            .btn-primary { background-color: #003366 !important; border-color: #003366 !important; }
            .btn-warning { background-color: #D4AF37 !important; border-color: #D4AF37 !important; color: white !important;}
            .btn-suite { background-color: white; color: #D4AF37; border: 2px solid #D4AF37; border-radius: 50px; padding: 5px 20px; font-weight: bold; transition: all 0.3s ease; }
            .btn-anim:hover { transform: scale(1.05); box-shadow: 0 5px 15px rgba(0,0,0,0.2) !important; }
            .btn-suite:hover { background-color: #D4AF37; color: white; transform: scale(1.05); }
            .filter-box { background-color: #2C3E50; padding: 15px; border-radius: 10px; margin-top: auto; margin-bottom: 20px; }
            .nav-link-custom { color: rgba(255,255,255,0.8) !important; font-size: 1.1rem; margin-bottom: 10px; transition: 0.3s; }
            .nav-link-custom:hover { padding-left: 20px; color: white !important; }
            .nav-link-custom.active { background-color: #D4AF37 !important; color: white !important; font-weight: bold; }
            @keyframes slideInLeft { from { opacity: 0; transform: translateX(-50px); } to { opacity: 1; transform: translateX(0); } }
            .fade-in-left { animation: slideInLeft 0.8s ease-out forwards; }
            @keyframes fadeInUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
            .fade-in-up { animation: fadeInUp 0.8s ease-out forwards; }
            @media print { .no-print { display: none !important; } #page-content { margin-left: 0 !important; width: 100%; padding: 0 !important; background-color: white !important;} }
        </style>
    </head>
    <body>{%app_entry%}<footer>{%config%}{%scripts%}{%renderer%}</footer></body>
</html>
'''
app.clientside_callback("""function(n) { if (n > 0) { window.print(); } return ""; }""", Output("btn-print", "children"), Input("btn-print", "n_clicks"), prevent_initial_call=True)

if __name__ == '__main__':
    url = "http://127.0.0.1:8050/"
    def open_browser():
        print("Vérification serveur...")
        for i in range(40):
            try:
                if requests.get(url, timeout=0.2).status_code == 200:
                    import webbrowser
                    webbrowser.open(url)
                    return
            except: time.sleep(0.5)
        print("Serveur lent : ouvrez le navigateur manuellement.")
    threading.Thread(target=open_browser).start()
    app.run(debug=False)