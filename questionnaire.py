import dash
from dash import html, dcc, Input, Output, State
import sqlite3

# 1. Initialisation de l'application
app = dash.Dash(__name__)

# 2. Définition de la mise en page (Layout)
# C'est ici qu'on définit l'apparence visuelle de la page
app.layout = html.Div([
    html.H1("Mon Questionnaire"),
    
    # Champ : Mode (Texte simple)
    html.Div([
        html.Label("Mode : "),
        dcc.Input(id='input-mode', type='text', placeholder="Ex: Normal")
    ], style={'padding': 10}),

    # Champ : Durée (Nombre)
    html.Div([
        html.Label("Durée (min) : "),
        dcc.Input(id='input-duree', type='number', placeholder="Ex: 60")
    ], style={'padding': 10}),

    # Champ : Sexe (Menu déroulant pour éviter les fautes de frappe)
    html.Div([
        html.Label("Sexe : "),
        dcc.Dropdown(
            id='input-sexe',
            options=['Homme', 'Femme', 'Autre'],
            value='Homme' # Valeur par défaut
        )
    ], style={'padding': 10, 'width': '300px'}), # un peu de style pour la largeur

    # Champ : Age (Nombre)
    html.Div([
        html.Label("Age : "),
        dcc.Input(id='input-age', type='number', placeholder="Ex: 30")
    ], style={'padding': 10}),

    # Bouton de validation
    html.Button('Valider', id='bouton-valider', n_clicks=0),

    # Zone pour afficher le résultat (juste pour confirmer que ça marche)
    html.Div(id='zone-resultat', style={'marginTop': 20, 'color': 'blue'})
])

# 3. La logique (Callback)
# Cette fonction fait le lien entre l'interface et le code Python
@app.callback(
    Output('zone-resultat', 'children'),      # Où va le résultat visuel
    Input('bouton-valider', 'n_clicks'),      # Ce qui déclenche l'action (le clic)
    State('input-mode', 'value'),             # Les données à récupérer (Mode)
    State('input-duree', 'value'),            # Les données à récupérer (Durée)
    State('input-sexe', 'value'),             # Les données à récupérer (Sexe)
    State('input-age', 'value'),              # Les données à récupérer (Age)
)
def recuperer_donnees(n_clicks, mode, duree, sexe, age):
    # On ne fait rien tant que le bouton n'a pas été cliqué au moins une fois
    if n_clicks == 0:
        return ""

    # --- C'EST ICI QUE TU RÉCUPÈRES TES VALEURS EN PYTHON ---
    # Tu peux les enregistrer dans une base de données, faire un calcul, etc.
    print(f"Nouvelle entrée reçue -> Mode: {mode}, Durée: {duree}, Sexe: {sexe}, Age: {age}")
    
    # On retourne un message à afficher sur la page web
    message = f"Données enregistrées : {mode} / {duree} min / {sexe} / {age} ans"

    conn = sqlite3.connect("../database.db")

    cur = conn.cursor()

    cur.execute(
        f"""
        INSERT INTO entretien (mode, duree, sexe, age) 
        VALUES ('{mode}', {duree}, '{sexe}', {age});
        """
    )

    conn.commit()
    conn.close()
    return message

# 4. Lancement du serveur
if __name__ == '__main__':
    app.run(debug=True)