import os
from dash.testing.application_runners import import_app
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURATION AUTOMATIQUE ---
driver_path = ChromeDriverManager().install()
driver_folder = os.path.dirname(driver_path)
os.environ["PATH"] += os.pathsep + driver_folder


# --- LE TEST ---
def test_mdd001_chargement_dashboard(dash_duo):
    
    # Démarrage de l'application
    app = import_app("app")
    dash_duo.start_server(app)

    # 1. Vérification du Titre (Déjà corrigé en MAJ)
    dash_duo.wait_for_text_to_equal("h3", "MDD VANNES", timeout=10)

    # 2. Vérification que la zone KPI est affichée
    dash_duo.wait_for_element("#kpi-container", timeout=4)
    
    # 3. Navigation vers "Données Brutes"
    dash_duo.find_element("a[href='/data']").click()
    
    # 4. Vérification que la page a changé
    # --- CORRECTION ICI : METTRE EN MAJUSCULES ---
    dash_duo.wait_for_text_to_equal("h2", "DONNÉES BRUTES", timeout=5)

    # 5. Vérification qu'il n'y a pas d'erreurs techniques
    assert dash_duo.get_logs() == [], "Des erreurs JS ont été détectées dans la console"