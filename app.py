import dash
from dash import dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import random

# =============================================================================
# 1. CRÉATION DES DONNÉES FICTIVES (EN MÉMOIRE UNIQUEMENT)
# =============================================================================
def generate_data():
    """
    Cette fonction invente 200 dossiers pour l'affichage.
    Aucun fichier n'est nécessaire.
    """
    print("Génération des données fictives...")
    
    # Listes de choix simples
    sexes = ['Femme', 'Femme', 'Femme', 'Homme', 'Homme'] # Plus de femmes pour le réalisme
    ages = [20, 25, 30, 35, 40, 45, 50, 60, 75]
    situations = ['Célibataire', 'Marié(e)', 'Divorcé(e)', 'Seul(e) avec enfants']
    orientations = ['Avocat', 'Notaire', 'Huissier', 'Médiateur', 'Police', 'CAF', 'Assistante Sociale']
    modes = ['Téléphone', 'Physique', 'Email']
    sources = ['Bouche à oreille', 'Mairie', 'Internet', 'Gendarmerie']

    data = []
    for i in range(200): # On crée 200 lignes
        data.append({
            'ID': i + 1,
            'Sexe': random.choice(sexes),
            'Age': random.choice(ages) + random.randint(-2, 2), # Ajoute un peu de variation
            'Situation': random.choice(situations),
            'Orientation': random.choice(orientations),
            'Mode_Contact': random.choice(modes),
            'Source': random.choice(sources)
        })
    
    return pd.DataFrame(data)

# On charge les données UNE SEULE FOIS au démarrage de l'app
df = generate_data()

# =============================================================================
# 2. CONFIGURATION DE L'APPLICATION (DESIGN PRO)
# =============================================================================
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.MINTY])
app.title = "Reporting Démo"

# Composant carte KPI (Chiffres clés en haut)
def draw_kpi(titre, valeur, couleur):
    return dbc.Card(
        dbc.CardBody([
            html.H2(valeur, className=f"text-{couleur}"),
            html.H6(titre, className="text-muted"),
        ]),
        className="text-center shadow-sm mb-4", 
        style={"border-top": f"4px solid {couleur}"}
    )

# =============================================================================
# 3. STRUCTURE DE LA PAGE (LAYOUT)
# =============================================================================
# Barre latérale (Menu)
sidebar = html.Div(
    [
        html.H3("⚖️ Reporting", className="display-6"),
        html.Hr(),
        dbc.Nav(
            [
                dbc.NavLink("📊 Vue Globale", href="/", active="exact"),
                dbc.NavLink("📋 Données", href="/data", active="exact"),
            ],
            vertical=True,
            pills=True,
        ),
    ],
    style={
        "position": "fixed", "top": 0, "left": 0, "bottom": 0, "width": "16rem",
        "padding": "2rem 1rem", "background-color": "#f8f9fa",
    },
)

content = html.Div(id="page-content", style={"margin-left": "18rem", "margin-right": "2rem", "padding": "2rem 1rem"})

app.layout = html.Div([dcc.Location(id="url"), sidebar, content])

# =============================================================================
# 4. LOGIQUE D'AFFICHAGE (CALLBACKS)
# =============================================================================
@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_content(pathname):
    
    if pathname == "/":
        # --- CALCULS AUTOMATIQUES ---
        total = len(df)
        top_orient = df['Orientation'].mode()[0]
        age_moyen = int(df['Age'].mean())

        # --- GRAPHIQUES ---
        # 1. Treemap (Carrés colorés) pour les Orientations
        fig_orient = px.treemap(df, path=['Orientation'], title="Répartition par Orientation",
                                color='Orientation', color_discrete_sequence=px.colors.qualitative.Pastel)
        
        # 2. Donut pour le Sexe
        fig_sexe = px.pie(df, names='Sexe', title="Répartition Hommes/Femmes", hole=0.6,
                          color_discrete_sequence=['#ff9999','#66b3ff'])

        # 3. Barres pour le Mode de contact
        fig_mode = px.bar(df['Mode_Contact'].value_counts(), title="Modes de Contact",
                          color_discrete_sequence=['#99ff99'])
        fig_mode.update_layout(showlegend=False)

        # 4. Pyramide des âges simple
        fig_age = px.histogram(df, x="Age", nbins=10, title="Répartition par Âge",
                               color_discrete_sequence=['#ffcc99'])

        # --- AFFICHAGE DASHBOARD ---
        return html.Div([
            html.H2("Tableau de Bord - Démo"),
            html.P("Données générées automatiquement (Mode Simulation)", className="text-muted"),
            html.Hr(),

            # Ligne des KPIs
            dbc.Row([
                dbc.Col(draw_kpi("Dossiers Traités", str(total), "primary"), width=4),
                dbc.Col(draw_kpi("Orientation Principale", top_orient, "success"), width=4),
                dbc.Col(draw_kpi("Âge Moyen", f"{age_moyen} ans", "warning"), width=4),
            ]),

            # Onglets
            dbc.Tabs([
                dbc.Tab(label="📈 Activité", children=[
                    dbc.Row([
                        dbc.Col(dcc.Graph(figure=fig_orient), width=8),
                        dbc.Col(dcc.Graph(figure=fig_mode), width=4),
                    ], className="mt-4")
                ]),
                dbc.Tab(label="👥 Usagers", children=[
                    dbc.Row([
                        dbc.Col(dcc.Graph(figure=fig_sexe), width=6),
                        dbc.Col(dcc.Graph(figure=fig_age), width=6),
                    ], className="mt-4")
                ])
            ])
        ])

    elif pathname == "/data":
        # --- AFFICHAGE TABLEAU ---
        return html.Div([
            html.H3("Données Brutes (Fictives)"),
            dash_table.DataTable(
                data=df.to_dict('records'),
                columns=[{"name": i, "id": i} for i in df.columns],
                page_size=12,
                style_table={'overflowX': 'auto'},
                style_header={'backgroundColor': 'lightgrey', 'fontWeight': 'bold'},
                style_cell={'textAlign': 'left'}
            )
        ])
    
    return html.H1("404: Page introuvable")

# =============================================================================
# 5. LANCEMENT
# =============================================================================
if __name__ == '__main__':
    # Ouvre le navigateur automatiquement
    import webbrowser
    webbrowser.open("http://127.0.0.1:8050/")
    app.run(debug=True)