import dash
from dash import dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go

# --- CONFIGURATION & DESIGN ---
DB_NAME = 'maison_droit.db'

# Thème "MINTY" pour un look frais et professionnel
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.MINTY], suppress_callback_exceptions=True)
app.title = "Maison du Droit - Décisionnel"

# --- FONCTION D'ACCÈS AUX DONNÉES (ROBUSTE) ---
def get_data():
    """Récupère et nettoie les données depuis SQLite"""
    conn = sqlite3.connect(DB_NAME)
    query = """
        SELECT r.id_requete, r.sexe, r.age, r.situation_familiale, r.mode_entretien, r.profession,
               o.libelle as orientation, c.libelle as communication, d.libelle as domaine
        FROM REQUETE r
        LEFT JOIN ORIENTATION o ON r.code_orientation = o.code_orientation
        LEFT JOIN COMMUNICATION c ON r.code_com = c.code_com
        LEFT JOIN CONCERNE link ON r.id_requete = link.id_requete
        LEFT JOIN DOMAINE_PRECIS d ON link.code_domaine = d.code_domaine
    """
    try:
        df = pd.read_sql_query(query, conn)
    except Exception as e:
        print(f"Erreur SQL: {e}")
        df = pd.DataFrame()
    conn.close()
    
    # Nettoyage à la volée pour l'affichage
    if not df.empty:
        df['sexe'] = df['sexe'].fillna('Non précisé')
        df['orientation'] = df['orientation'].fillna('Sans suite / Inconnu')
        df['communication'] = df['communication'].fillna('Non renseigné')
        # On force l'âge en numérique, les erreurs deviennent NaN
        df['age'] = pd.to_numeric(df['age'], errors='coerce')
    return df

# --- COMPOSANTS REUTILISABLES ---
def draw_kpi_card(title, value, icon, color):
    """Crée une jolie carte pour les chiffres clés"""
    return dbc.Card(
        dbc.CardBody([
            html.Div([
                html.H4(value, className=f"text-{color}"),
                html.H6(title, className="text-muted"),
            ], style={'flex': '1'}),
            html.Div(icon, style={'fontSize': '2rem', 'color': '#ccc'})
        ], className="d-flex align-items-center"),
        className="mb-4 shadow-sm", style={"border-left": f"5px solid {color}"}
    )

# --- LAYOUT (STRUCTURE) ---
sidebar = html.Div(
    [
        html.Div([
            # Tu pourrais mettre un logo ici avec html.Img
            html.H3("⚖️ MDD Vannes", className="display-7 fw-bold"),
            html.P("Outil Décisionnel", className="text-muted small")
        ], className="mb-4 text-center"),
        
        dbc.Nav(
            [
                dbc.NavLink("📊 Tableau de Bord", href="/", active="exact", className="mb-2"),
                dbc.NavLink("📋 Données Brutes", href="/data", active="exact", className="mb-2"),
                dbc.NavLink("⚙️ Export & Admin", href="/admin", active="exact"),
            ],
            vertical=True,
            pills=True,
        ),
        
        html.Div([
            html.Hr(),
            html.Small("SAE 5.VCOD.01", className="text-muted"),
            html.Br(),
            html.Small("© 2025 Trinôme RMA", className="text-muted")
        ], style={"position": "absolute", "bottom": "20px"})
    ],
    style={
        "position": "fixed", "top": 0, "left": 0, "bottom": 0, "width": "16rem",
        "padding": "2rem 1rem", "background-color": "#f8f9fa", "border-right": "1px solid #dee2e6"
    },
)

content = html.Div(id="page-content", style={"margin-left": "17rem", "margin-right": "1rem", "padding": "2rem 1rem"})

app.layout = html.Div([dcc.Location(id="url"), sidebar, content])

# --- LOGIQUE (CALLBACKS) ---
@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_page_content(pathname):
    df = get_data()
    
    if df.empty:
        return dbc.Alert([
            html.H4("Base de données vide ou inaccessible", className="alert-heading"),
            html.P("Veuillez lancer le script 'etl.py' pour importer les données Excel.")
        ], color="danger")

    if pathname == "/":
        return layout_dashboard(df)
    elif pathname == "/data":
        return layout_datatable(df)
    elif pathname == "/admin":
        return layout_admin()
    
    return dbc.Container(html.H1("404: Page introuvable", className="text-danger"))

def layout_dashboard(df):
    # --- CALCULS KPI ---
    total_req = len(df)
    top_orient = df['orientation'].mode()[0] if not df['orientation'].empty else "-"
    moyenne_age = round(df['age'].mean()) if not df['age'].isnull().all() else "-"
    top_source = df['communication'].mode()[0] if not df['communication'].empty else "-"

    # --- GRAPHIQUES ---
    
    # 1. Onglet ACTIVITÉ
    # Treemap des Orientations (Plus joli qu'un bar chart quand il y a beaucoup de catégories)
    df_orient = df['orientation'].value_counts().reset_index()
    df_orient.columns = ['Label', 'Value']
    fig_treemap = px.treemap(df_orient, path=['Label'], values='Value', color='Value', 
                             color_continuous_scale='Teal', title="Cartographie des Orientations")
    
    # Bar chart Modes
    df_mode = df['mode_entretien'].value_counts().reset_index()
    fig_mode = px.bar(df_mode, x='mode_entretien', y='count', title="Modes de contact", 
                      text_auto=True, color_discrete_sequence=['#78C2AD'])

    # 2. Onglet SOCIOLOGIE
    # Donut Sexe
    fig_sexe = px.pie(df, names='sexe', title="Répartition H/F", hole=0.5, 
                      color_discrete_sequence=px.colors.qualitative.Pastel)
    
    # Histogramme Age
    fig_age = px.histogram(df, x="age", nbins=10, title="Pyramide des âges", 
                           color_discrete_sequence=['#F3969A'])
    
    # Bar Chart Situation Familiale
    df_fam = df['situation_familiale'].value_counts().head(8).reset_index() # Top 8 pour lisibilité
    fig_fam = px.bar(df_fam, x='count', y='situation_familiale', orientation='h', 
                     title="Situation Familiale", color_discrete_sequence=['#6CC3D5'])

    # 3. Onglet ORIGINE
    # Sunburst (Source de communication)
    df_com = df['communication'].value_counts().reset_index()
    fig_sunburst = px.sunburst(df_com, path=['communication'], values='count', 
                               title="Comment nous ont-ils connus ?", color_discrete_sequence=px.colors.sequential.Mint)

    return html.Div([
        # En-tête
        dbc.Row([
            dbc.Col(html.H2("Vue d'ensemble 2024-2025"), width=8),
            dbc.Col(html.Div("Dernière MAJ: Aujourd'hui", className="text-muted text-end"), width=4)
        ], className="mb-4"),

        # Ligne de KPIs
        dbc.Row([
            dbc.Col(draw_kpi_card("Total Dossiers", str(total_req), "📁", "primary"), width=3),
            dbc.Col(draw_kpi_card("Orientation Top 1", top_orient[:15]+"...", "📍", "success"), width=3),
            dbc.Col(draw_kpi_card("Âge Moyen", f"{moyenne_age} ans", "🎂", "warning"), width=3),
            dbc.Col(draw_kpi_card("Source Top 1", top_source[:15]+"...", "📢", "info"), width=3),
        ]),

        # Les Onglets (Le cœur de l'app Pro)
        dbc.Tabs([
            # ONGLET 1 : ACTIVITÉ
            dbc.Tab(label="📈 Activité & Solutions", children=[
                dbc.Row([
                    dbc.Col(dcc.Graph(figure=fig_treemap), width=8),
                    dbc.Col(dcc.Graph(figure=fig_mode), width=4),
                ], className="mt-3")
            ]),

            # ONGLET 2 : USAGERS
            dbc.Tab(label="👥 Profil des Usagers", children=[
                dbc.Row([
                    dbc.Col(dcc.Graph(figure=fig_sexe), width=4),
                    dbc.Col(dcc.Graph(figure=fig_age), width=4),
                    dbc.Col(dcc.Graph(figure=fig_fam), width=4),
                ], className="mt-3")
            ]),

            # ONGLET 3 : COMMUNICATION
            dbc.Tab(label="📣 Communication", children=[
                dbc.Row([
                    dbc.Col(dcc.Graph(figure=fig_sunburst), width=6),
                    dbc.Col(dbc.Card([
                        dbc.CardHeader("Analyse"),
                        dbc.CardBody("Ce graphique permet de visualiser les canaux de communication les plus efficaces pour orienter les budgets publicitaires de l'association.")
                    ], color="light", className="mt-5"), width=6)
                ], className="mt-3")
            ]),
        ])
    ])

def layout_datatable(df):
    return html.Div([
        html.H2("Exploration des Données"),
        html.P("Tableau interactif : vous pouvez trier et filtrer les colonnes."),
        html.Hr(),
        dash_table.DataTable(
            data=df.to_dict('records'),
            columns=[{"name": i, "id": i} for i in df.columns if i != 'id_requete'],
            page_size=15,
            sort_action="native",
            filter_action="native",
            style_table={'overflowX': 'auto'},
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            },
            style_cell={
                'textAlign': 'left',
                'padding': '10px',
                'fontFamily': 'sans-serif'
            }
        )
    ])

def layout_admin():
    return html.Div([
        html.H2("Administration"),
        dbc.Alert("Section réservée à la maintenance.", color="warning"),
        html.P("Fonctionnalités futures :"),
        html.Ul([
            html.Li("Gestion des utilisateurs"),
            html.Li("Sauvegarde de la base de données"),
            html.Li("Logs d'erreurs ETL")
        ]),
        dbc.Button("📥 Télécharger un rapport PDF (Démo)", color="dark", outline=True)
    ])

if __name__ == '__main__':
    app.run(debug=True)