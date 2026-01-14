import dash
from dash import dcc, html, Input, Output, State, dash_table, ctx
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import threading
import time
import requests 
import psycopg2 
import json
import os
from datetime import datetime

# =============================================================================
# 1. CONFIGURATION & MAPPINGS
# =============================================================================
COLOR_NAVY = "#003366"
COLOR_GOLD = "#D4AF37"
COLOR_BG = "#F4F6F9"

TRANSCO_MODE = {1: "RDV", 2: "Sans RDV", 3: "Téléphone", 4: "Courrier", 5: "Mail"}
TRANSCO_SEXE = {1: "Homme", 2: "Femme", 3: "Couple", 4: "Pro"}
TRANSCO_AGE = {1: "-18 ans", 2: "18-25 ans", 3: "26-40 ans", 4: "41-60 ans", 5: "+ 60 ans"}
TRANSCO_SIT = {"1": "Célibataire", "2": "Concubin", "3": "Pacsé", "4": "Marié", "5": "Séparé/Div", "5a": "Sép. s/s enf", "5b": "Sép. Alt", "5c": "Sép. Princ", "5d": "Sép. Visite", "5e": "Parent Isolé", "5f": "Sép. m. toit", "6": "Veuf/ve", "7": "Non Rens."}
TRANSCO_VIENT = {1: "Soi", 2: "Conjoint", 3: "Parent", 4: "Enfant", 5: "Pers. Morale", 6: "Autre"}
TRANSCO_PROF = {1: "Scolaire/Etu", 2: "Agri/Pêche", 3: "Chef Ent.", 4: "Libéral", 5: "Militaire", 6: "Employé", 7: "Ouvrier", 8: "Cadre", 9: "Retraité", 10: "Chômeur", 11: "Sans Prof."}
TRANSCO_DUREE = {1: "- 15 min", 2: "15-30 min", 3: "30-45 min", 4: "45-60 min", 5: "+ 60 min"}
TRANSCO_RESS = {1: "Salaire", 2: "Rev. Pro", 3: "Retraite", 4: "Chômage", 5: "RSA", 6: "AAH", 7: "IJSS", 8: "Bourse", 9: "Sans", 10: "Autre"}

# Inversés pour la saisie
REV_MODE = {v: k for k, v in TRANSCO_MODE.items()}
REV_SEXE = {v: k for k, v in TRANSCO_SEXE.items()}
REV_AGE = {v: k for k, v in TRANSCO_AGE.items()}
REV_SIT = {v: k for k, v in TRANSCO_SIT.items()}
REV_VIENT = {v: k for k, v in TRANSCO_VIENT.items()}
REV_PROF = {v: k for k, v in TRANSCO_PROF.items()}
REV_DUREE = {v: k for k, v in TRANSCO_DUREE.items()}
REV_RESS = {v: k for k, v in TRANSCO_RESS.items()}

# =============================================================================
# 2. GESTION BASE DE DONNÉES
# =============================================================================
def get_db_connection():
    if not os.path.exists('config.json'): return None
    config = json.load(open('config.json', 'r', encoding='utf-8'))
    return psycopg2.connect(**config['POSTGRES'])

def load_data_from_db():
    # print("🔄 Chargement des données...")
    try:
        conn = get_db_connection()
        if not conn: return pd.DataFrame()
        
        query = """
            SELECT e.num, e.date_ent, e.mode, e.duree, e.sexe, e.age, e.vient_pr, e.sit_fam, 
                   e.enfant, e.modele_fam, e.profession, e.ress, e.origine, e.commune, e.partenaire,
                   STRING_AGG(DISTINCT d.nature, ', ') as demande_txt,
                   STRING_AGG(DISTINCT s.nature, ', ') as solution_txt
            FROM entretien e
            LEFT JOIN demande d ON e.num = d.num
            LEFT JOIN solution s ON e.num = s.num
            GROUP BY e.num
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty: return pd.DataFrame()

        # Nettoyage Dates et Années
        df['date_ent'] = pd.to_datetime(df['date_ent'], errors='coerce')
        # Création colonne Année robuste
        df['Annee'] = df['date_ent'].apply(lambda x: str(x.year) if pd.notnull(x) else "Inconnue")
        df['Mois'] = df['date_ent'].dt.strftime('%Y-%m')

        # Mapping 
        df['Mode_Lib'] = df['mode'].map(TRANSCO_MODE).fillna('Autre')
        df['Sexe_Lib'] = df['sexe'].map(TRANSCO_SEXE).fillna('Inc.')
        df['Age_Lib'] = df['age'].map(TRANSCO_AGE).fillna('Inc.')
        df['Sit_Lib'] = df['sit_fam'].astype(str).map(TRANSCO_SIT).fillna(df['sit_fam'])
        df['Prof_Lib'] = df['profession'].map(TRANSCO_PROF).fillna('Autre')
        
        df.rename(columns={'commune': 'Ville', 'partenaire': 'Partenaire', 'num': 'N° Dossier', 
                           'demande_txt': 'Demandes', 'solution_txt': 'Solutions'}, inplace=True)
        
        for col in ['Ville', 'Partenaire', 'modele_fam', 'Demandes', 'Solutions']:
            df[col] = df[col].astype(str).str.strip().str.replace("''", "'").replace("nan", "").replace("None", "").replace("NULL", "")

        return df.sort_values('date_ent', ascending=False)

    except Exception as e:
        print(f"❌ ERREUR SQL : {e}")
        return pd.DataFrame()

df_global = load_data_from_db()

# =============================================================================
# 3. INTERFACE DASH
# =============================================================================
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LUX], suppress_callback_exceptions=True)
app.title = "MDD Manager"

sidebar = html.Div([
    html.H3("MDD Vannes", className="text-center mb-4", style={'color': COLOR_GOLD}),
    dbc.Nav([
        dbc.NavLink("📊 Tableau de Bord", href="/", active="exact", className="nav-link-custom"),
        dbc.NavLink("📋 Données Brutes", href="/data", active="exact", className="nav-link-custom"),
        dbc.NavLink("📝 Nouvelle Saisie", href="/input", active="exact", className="nav-link-custom"),
    ], vertical=True, pills=True, className="mb-4"),
    
    html.Div([
        html.H5("FILTRES", style={'color': COLOR_GOLD, 'borderBottom': '1px solid white'}),
        html.Label("Année", style={'color': 'white'}),
        
        # --- CORRECTION ICI : STYLE COLOR BLACK ---
        dcc.Dropdown(id='filter-year', options=[], value='ALL', clearable=False, 
                     style={'color': 'black'}), # Texte noir pour être lisible
    ], className="filter-box")
], style={"position": "fixed", "top": 0, "left": 0, "bottom": 0, "width": "18rem", "padding": "2rem 1rem", "background-color": COLOR_NAVY, "color": "white", "overflowY": "auto"})

content = html.Div(id="page-content", style={"margin-left": "20rem", "padding": "2rem", "backgroundColor": COLOR_BG, "minHeight": "100vh"})

app.layout = html.Div([
    dcc.Location(id="url"),
    dcc.Store(id='refresh-trigger', data=0),
    sidebar, 
    content
])

def insert_entretien_complet(data):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        sql_ent = """
            INSERT INTO entretien (date_ent, mode, duree, sexe, age, vient_pr, sit_fam, 
                                   enfant, modele_fam, profession, ress, origine, commune, partenaire)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING num;
        """
        cur.execute(sql_ent, (
            data['date'], data['mode'], data['duree'], data['sexe'], data['age'], 
            data['vient'], data['sit'], data['enfant'], data['mod_fam'], 
            data['prof'], data['ress'], data['origine'], data['ville'], data['partenaire']
        ))
        new_id = cur.fetchone()[0]
        if data['demande_txt']:
            cur.execute(f"INSERT INTO demande (num, pos, nature) VALUES ({new_id}, 1, '{data['demande_txt'].replace("'", "''")}')")
        if data['solution_txt']:
            cur.execute(f"INSERT INTO solution (num, pos, nature) VALUES ({new_id}, 1, '{data['solution_txt'].replace("'", "''")}')")
        conn.commit()
        conn.close()
        return True, f"Dossier N°{new_id} enregistré avec succès !"
    except Exception as e:
        if conn: conn.rollback()
        return False, f"Erreur SQL : {str(e)}"

# =============================================================================
# 4. CALLBACKS
# =============================================================================

# --- CALLBACK : MET À JOUR LE FILTRE ANNÉE ---
@app.callback(
    Output('filter-year', 'options'),
    [Input('url', 'pathname'), Input('refresh-trigger', 'data')]
)
def update_year_filter(path, refresh):
    if df_global.empty: return [{'label': 'Aucune donnée', 'value': 'ALL'}]
    years = sorted(df_global['Annee'].unique(), reverse=True)
    return [{'label': 'Tout', 'value': 'ALL'}] + [{'label': y, 'value': y} for y in years if y != "Inconnue"]

@app.callback(Output("page-content", "children"), [Input("url", "pathname"), Input("refresh-trigger", "data")])
def render_page_content(pathname, refresh):
    global df_global
    if ctx.triggered_id == "refresh-trigger" or pathname: 
        df_global = load_data_from_db()

    if pathname == "/data":
        return html.Div([
            html.H2("Données Brutes", style={'color': COLOR_NAVY}),
            dash_table.DataTable(
                data=df_global.to_dict('records'),
                columns=[{"name": i, "id": i} for i in ['date_ent', 'Ville', 'Mode_Lib', 'Sit_Lib', 'Demandes', 'Solutions'] if i in df_global.columns],
                page_size=15, style_header={'backgroundColor': COLOR_NAVY, 'color': 'white'},
                style_cell={'textAlign': 'left', 'whiteSpace': 'normal', 'height': 'auto'},
            )
        ])
    elif pathname == "/input":
        return html.Div([
            html.H2("📝 Saisie d'un nouvel entretien", style={'color': COLOR_NAVY, 'marginBottom': '20px'}),
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([html.Label("Date", className="fw-bold"), dcc.DatePickerSingle(id='in-date', date=datetime.today().date(), display_format='DD/MM/YYYY', style={'width': '100%'})], width=3),
                        dbc.Col([html.Label("Mode", className="fw-bold"), dcc.Dropdown(id='in-mode', options=[{'label': v, 'value': v} for v in TRANSCO_MODE.values()], placeholder="Mode")], width=3),
                        dbc.Col([html.Label("Durée", className="fw-bold"), dcc.Dropdown(id='in-duree', options=[{'label': v, 'value': v} for v in TRANSCO_DUREE.values()], placeholder="Durée")], width=3),
                        dbc.Col([html.Label("Partenaire"), dbc.Input(id='in-partenaire', placeholder="Ex: Notaire")], width=3),
                    ], className="mb-3"),
                    dbc.Row([
                        dbc.Col([html.Label("Sexe", className="fw-bold"), dcc.Dropdown(id='in-sexe', options=[{'label': v, 'value': v} for v in TRANSCO_SEXE.values()])], width=3),
                        dbc.Col([html.Label("Tranche d'Age"), dcc.Dropdown(id='in-age', options=[{'label': v, 'value': v} for v in TRANSCO_AGE.values()])], width=3),
                        dbc.Col([html.Label("Ville"), dbc.Input(id='in-ville', placeholder="Ex: Vannes")], width=3),
                        dbc.Col([html.Label("Nb Enfants"), dbc.Input(id='in-enfant', type="number", min=0, value=0)], width=3),
                    ], className="mb-3"),
                    dbc.Row([
                        dbc.Col([html.Label("Situation Familiale"), dcc.Dropdown(id='in-sit', options=[{'label': v, 'value': v} for v in TRANSCO_SIT.values()])], width=4),
                        dbc.Col([html.Label("Modèle Familial"), dbc.Input(id='in-mod-fam', placeholder="Ex: 5c")], width=4),
                        dbc.Col([html.Label("Vient pour"), dcc.Dropdown(id='in-vient', options=[{'label': v, 'value': v} for v in TRANSCO_VIENT.values()])], width=4),
                    ], className="mb-3"),
                    dbc.Row([
                        dbc.Col([html.Label("Profession"), dcc.Dropdown(id='in-prof', options=[{'label': v, 'value': v} for v in TRANSCO_PROF.values()])], width=4),
                        dbc.Col([html.Label("Ressources"), dcc.Dropdown(id='in-ress', options=[{'label': v, 'value': v} for v in TRANSCO_RESS.values()])], width=4),
                        dbc.Col([html.Label("Origine"), dbc.Input(id='in-origine', placeholder="Ex: 1a")], width=4),
                    ], className="mb-4"),
                    html.Hr(),
                    dbc.Row([
                        dbc.Col([html.Label("🔎 Demande", className="fw-bold text-primary"), dbc.Textarea(id='in-demande-txt', style={'height': '100px'})], width=6),
                        dbc.Col([html.Label("💡 Solution", className="fw-bold text-success"), dbc.Textarea(id='in-solution-txt', style={'height': '100px'})], width=6),
                    ], className="mb-4"),
                    dbc.Button("💾 Enregistrer", id="btn-submit", color="primary", size="lg", className="w-100 shadow"),
                    html.Br(), html.Br(),
                    html.Div(id="submit-feedback")
                ])
            ], className="shadow-sm")
        ])
    
    return html.Div([
        html.H2("Tableau de Bord", style={'color': COLOR_NAVY}),
        html.Div(id="kpi-container"),
        html.Hr(),
        html.Div([
            dbc.Button("📊 Activité", id="btn-act", color="primary", className="me-2"),
            dbc.Button("👥 Usagers", id="btn-cli", color="light", className="me-2"),
            dbc.Button("📈 Évolution", id="btn-evo", color="light", className="me-2"),
        ], className="mb-3"),
        html.Div(id="graphs-container")
    ])

@app.callback(
    [Output("kpi-container", "children"), Output("graphs-container", "children"),
     Output("btn-act", "color"), Output("btn-cli", "color"), Output("btn-evo", "color")],
    [Input("filter-year", "value"), Input("btn-act", "n_clicks"), Input("btn-cli", "n_clicks"), Input("btn-evo", "n_clicks")]
)
def update_dashboard(fy, b1, b2, b3):
    ctx_id = ctx.triggered_id if ctx.triggered else "btn-act"
    view = "act"
    if ctx_id == "btn-cli": view = "cli"
    elif ctx_id == "btn-evo": view = "evo"

    dff = df_global.copy()
    if df_global.empty: return html.Div("Pas de données"), html.Div(), "light", "light", "light"
    if fy != 'ALL' and fy is not None: dff = dff[dff['Annee'] == fy]

    kpi = dbc.Row([
        dbc.Col(dbc.Card([html.H2(len(dff), className="text-warning"), html.H6("Total")], body=True, className="text-center shadow-sm"), width=3),
        dbc.Col(dbc.Card([html.H2(dff['Ville'].mode()[0] if not dff.empty else "-", className="text-primary"), html.H6("Top Ville")], body=True, className="text-center shadow-sm"), width=3),
        dbc.Col(dbc.Card([html.H2(dff['Sit_Lib'].mode()[0] if not dff.empty else "-", className="text-primary", style={'fontSize': '1rem'}), html.H6("Situation")], body=True, className="text-center shadow-sm"), width=3),
        dbc.Col(dbc.Card([html.H2(dff['Prof_Lib'].mode()[0] if not dff.empty else "-", className="text-primary", style={'fontSize': '1rem'}), html.H6("Profession")], body=True, className="text-center shadow-sm"), width=3),
    ], className="mb-4")

    graphs = []
    colors = ["light", "light", "light"]
    if view == "act":
        colors[0] = "primary"
        df_part = dff[dff['Partenaire'] != ""]
        fig1 = px.bar(dff['Mode_Lib'].value_counts(), title="Modes", color_discrete_sequence=[COLOR_NAVY])
        fig2 = px.bar(df_part['Partenaire'].value_counts().head(10), orientation='h', title="Top Partenaires", color_discrete_sequence=[COLOR_GOLD])
        graphs = [dbc.Row([dbc.Col(dcc.Graph(figure=fig1), width=6), dbc.Col(dcc.Graph(figure=fig2), width=6)])]
    elif view == "cli":
        colors[1] = "primary"
        graphs = [
            dbc.Row([dbc.Col(dcc.Graph(figure=px.bar(dff['Age_Lib'].value_counts(), title="Age", color_discrete_sequence=[COLOR_NAVY])), width=6), dbc.Col(dcc.Graph(figure=px.pie(dff, names='Sexe_Lib', title="Sexe", hole=0.4, color_discrete_sequence=[COLOR_NAVY, COLOR_GOLD])), width=6)]),
            dbc.Row([dbc.Col(dcc.Graph(figure=px.bar(dff['Sit_Lib'].value_counts(), title="Situation", color_discrete_sequence=[COLOR_GOLD])), width=6), dbc.Col(dcc.Graph(figure=px.pie(dff, names='Prof_Lib', title="Profession", color_discrete_sequence=px.colors.sequential.Blues)), width=6)])
        ]
    elif view == "evo":
        colors[2] = "primary"
        df_evol = dff.groupby('Mois').size().reset_index(name='Nombre')
        graphs = [dbc.Row([dbc.Col(dcc.Graph(figure=px.line(df_evol, x='Mois', y='Nombre', title="Evolution Mensuelle", markers=True, color_discrete_sequence=[COLOR_NAVY])), width=12)])]

    return kpi, graphs, colors[0], colors[1], colors[2]

@app.callback(
    [Output("submit-feedback", "children"), Output("refresh-trigger", "data")],
    [Input("btn-submit", "n_clicks")],
    [State('in-date', 'date'), State('in-mode', 'value'), State('in-duree', 'value'), State('in-sexe', 'value'), State('in-age', 'value'), State('in-ville', 'value'), State('in-enfant', 'value'), State('in-sit', 'value'), State('in-mod-fam', 'value'), State('in-vient', 'value'), State('in-prof', 'value'), State('in-ress', 'value'), State('in-origine', 'value'), State('in-partenaire', 'value'), State('in-demande-txt', 'value'), State('in-solution-txt', 'value')],
    prevent_initial_call=True
)
def save_form_data(n, date, mode, duree, sexe, age, ville, enfant, sit, mod_fam, vient, prof, ress, origine, part, dem_txt, sol_txt):
    if not date or not mode or not sexe: return dbc.Alert("❌ Champs obligatoires manquants.", color="danger"), dash.no_update
    try:
        data = {'date': date, 'mode': REV_MODE.get(mode), 'duree': REV_DUREE.get(duree, 2), 'sexe': REV_SEXE.get(sexe), 'age': REV_AGE.get(age, 0), 'ville': ville if ville else "", 'enfant': int(enfant) if enfant else 0, 'sit': REV_SIT.get(sit, "7"), 'mod_fam': mod_fam if mod_fam else None, 'vient': REV_VIENT.get(vient, 6), 'prof': REV_PROF.get(prof, 11), 'ress': REV_RESS.get(ress, 9), 'origine': origine if origine else None, 'partenaire': part if part else "", 'demande_txt': dem_txt, 'solution_txt': sol_txt}
        success, msg = insert_entretien_complet(data)
        return (dbc.Alert(f"✅ {msg}", color="success"), time.time()) if success else (dbc.Alert(f"❌ {msg}", color="danger"), dash.no_update)
    except Exception as e: return dbc.Alert(f"❌ Erreur: {str(e)}", color="danger"), dash.no_update

app.index_string = '''<!DOCTYPE html><html><head>{%metas%}<title>MDD</title>{%favicon%}{%css%}<style>.nav-link-custom { color: rgba(255,255,255,0.8) !important; }.nav-link-custom.active { background-color: #D4AF37 !important; color: white !important; font-weight: bold; }.filter-box { background-color: #2C3E50; padding: 15px; border-radius: 10px; margin-top: 20px; }</style></head><body>{%app_entry%}<footer>{%config%}{%scripts%}{%renderer%}</footer></body></html>'''

if __name__ == '__main__':
    url = "http://127.0.0.1:8050/"
    def open_browser():
        time.sleep(1)
        try: requests.get(url); import webbrowser; webbrowser.open(url)
        except: pass
    threading.Thread(target=open_browser).start()
    app.run(debug=True)