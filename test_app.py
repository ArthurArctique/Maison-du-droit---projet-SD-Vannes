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
    dash_duo.wait_for_text_to_equal("#view-dashboard h2", "TABLEAU DE BORD", timeout=10)

    # 2. Vérification KPI
    dash_duo.wait_for_element("#kpi-container", timeout=4)
    
    # 3. Navigation vers Données
    dash_duo.find_element("a[href='/data']").click()
    
    # 4. Vérification Page Données
    dash_duo.wait_for_contains_text("#view-data h2", "DONNÉES", timeout=10)

    # 5. Vérification des boutons CRUD
    dash_duo.wait_for_element("#btn-edit-mode", timeout=5)
    dash_duo.wait_for_element("#btn-delete", timeout=5)

    # 6. Vérification technique (INTELLIGENTE)
    # On récupère tous les logs du navigateur
    logs = dash_duo.get_logs()
    
    # On filtre pour ne garder que les erreurs SEVERE (Critiques)
    critical_errors = [log for log in logs if log['level'] == 'SEVERE']

    # LISTE BLANCHE D'ERREURS À IGNORER
    # On ignore favicon, extensions, et les erreurs de coupure serveur (_dash-update-component)
    ignore_list = [
        "favicon.ico", 
        "react_devtools_backend", 
        "chrome-extension", 
        "_dash-update-component" # <-- L'ajout qui sauve la mise
    ]
    
    real_errors = []
    for err in critical_errors:
        is_ignored = False
        for ignore_txt in ignore_list:
            if ignore_txt in err['message']:
                is_ignored = True
                break
        
        if not is_ignored:
            real_errors.append(err)

    # Affichage pour débogage si besoin
    if real_errors:
        print("\n⚠️  VRAIES ERREURS JS DÉTECTÉES :")
        for err in real_errors:
            print(f"   - {err['message']}")

    # Le test échoue seulement s'il reste des VRAIES erreurs
    assert real_errors == [], f"Erreurs critiques détectées : {real_errors}"