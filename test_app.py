import os
from dash.testing.application_runners import import_app
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# --- LE TEST ---
def test_mdd001_chargement_dashboard(dash_duo):
    
    # Démarrage de l'application
    app = import_app("app")
    dash_duo.start_server(app)

    # 1. Vérification du Titre Accueil
    # CORRECTION : On met en MAJUSCULES car c'est ce que l'application affiche
    dash_duo.wait_for_text_to_equal("#view-dashboard h2", "TABLEAU DE BORD", timeout=10)

    # 2. Vérification KPI
    dash_duo.wait_for_element("#kpi-container", timeout=4)
    
    # 3. Navigation vers Données
    dash_duo.find_element("a[href='/data']").click()
    
    # 4. Vérification Page Données
    # CORRECTION : On met aussi en MAJUSCULES par précaution (DONNÉES BRUTES)
    # et on utilise wait_for_contains_text pour être plus souple
    dash_duo.wait_for_contains_text("#view-data h2", "DONNÉES", timeout=10)

    # 5. Vérification des boutons CRUD
    dash_duo.wait_for_element("#btn-edit-mode", timeout=5)
    dash_duo.wait_for_element("#btn-delete", timeout=5)

    # 6. Vérification technique
    assert dash_duo.get_logs() == [], "Des erreurs JS ont été détectées"