import pytest
import pandas as pd
from unittest.mock import MagicMock
import app
from dash import no_update

# =============================================================================
# 1. TESTS DE CONFIGURATION (Dictionnaires)
# =============================================================================
def test_transco_dictionaries_integrity():
    """Vérifie les dictionnaires de traduction."""
    assert app.TRANSCO_MODE[1] == "RDV"
    assert app.REV_MODE["RDV"] == 1
    assert app.TRANSCO_SEXE[1] == "Homme"

# =============================================================================
# 2. TESTS LOGIQUE MÉTIER (Load / Save / Excel)
# =============================================================================
@pytest.fixture
def mock_db_data():
    """
    Crée un faux DataFrame qui imite PARFAITEMENT le retour SQL brut.
    IMPORTANT : On met la date la plus récente sur la ligne 'RDV' (Mode 1)
    car l'app trie par date décroissante.
    """
    return pd.DataFrame({
        # Colonnes brutes (Codes SQL)
        'num': [101, 102],
        'date_ent': ['2023-02-01', '2023-01-15'], # Février (RDV) avant Janvier (Sans RDV)
        'mode': [1, 2], # 1=RDV, 2=Sans RDV
        'duree': [1, 2],
        'sexe': [2, 1],
        'age': [3, 2],
        'vient_pr': [1, 1],
        'sit_fam': ['4', '1'], # Codes en String comme dans la BDD
        'enfant': [2, 0],
        'modele_fam': [1, None],
        'profession': [6, 7],
        'ress': [1, 5],
        'origine': ['1a', None],
        'commune': ['Vannes', 'Auray'],
        'partenaire': ['CAF', ''],
        
        # Colonnes textes pour Demandes/Solutions (aggrégées par SQL normalement)
        'demande_txt': ['Logement', ''],
        'solution_txt': ['Avocat', '']
    })

def test_load_data_logic(mocker, mock_db_data):
    """Teste le chargement et la TRANSFORMATION des données."""
    mocker.patch('app.get_db_connection', return_value=MagicMock())
    # On simule que SQL retourne nos données brutes
    mocker.patch('pandas.read_sql_query', return_value=mock_db_data)
    
    df = app.load_data_from_db()
    
    # Vérifications
    assert not df.empty
    assert 'Ville' in df.columns # Vérifie le renommage commune -> Ville
    assert 'id' in df.columns    # Vérifie le renommage num -> id
    
    # Vérifie que le mapping a fonctionné ET que le tri est bon
    # Index 0 doit être le plus récent (2023-02-01) donc "RDV"
    assert df.iloc[0]['Mode_Lib'] == "RDV"

def test_save_entretien_db_logic(mocker):
    """Teste la logique SQL (Insert/Update)."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = [999]
    mocker.patch('app.get_db_connection', return_value=mock_conn)

    data = {'date': '2023-01-01', 'mode': 1, 'duree': 2, 'sexe': 1, 'age': 3, 
            'vient': 1, 'sit': '4', 'enfant': 0, 'mod_fam': 1, 'prof': 6, 
            'ress': 1, 'origine': '1a', 'ville': 'Vannes', 'partenaire': '', 
            'demande_txt': '', 'solution_txt': ''}

    # Test INSERT
    success, msg = app.save_entretien_db(data, update_id=None)
    assert success is True
    assert "créé" in msg

    # Test UPDATE
    success, msg = app.save_entretien_db(data, update_id=999)
    assert success is True
    assert "modifié" in msg

def test_export_excel_callback(mocker):
    """Teste le bouton Excel."""
    app.df_global = pd.DataFrame({'A': [1, 2]})
    res = app.export_excel_callback(1)
    assert res['filename'] == "export_mdd_vannes.xlsx"

def test_display_page():
    """Teste la navigation."""
    hide, show, hide2 = app.display_page("/data")
    assert show == {'display': 'block'}
    hide, hide2, show = app.display_page("/input")
    assert show == {'display': 'block'}
    show, hide, hide2 = app.display_page("/")
    assert show == {'display': 'block'}

def test_populate_form(mock_db_data, mocker):
    """Teste le pré-remplissage du formulaire."""
    # 1. On prépare les données comme si elles sortaient de load_data_from_db
    # (Il faut renommer 'num' en 'id' et ajouter les libellés, car populate_form utilise df_global)
    df_processed = mock_db_data.copy()
    df_processed.rename(columns={'num': 'id', 'commune': 'Ville', 'partenaire': 'Partenaire', 'demande_txt': 'Demandes', 'solution_txt': 'Solutions'}, inplace=True)
    
    # On ajoute les colonnes calculées manquantes pour éviter tout bug
    df_processed['Mode_Lib'] = "RDV"
    
    # On injecte dans l'app
    app.df_global = df_processed
    
    # Cas 1 : ID Inexistant
    res = app.populate_form(None)
    assert res[0] == "📝 Saisie d'un nouvel entretien"
    
    # Cas 2 : ID Existant (101)
    res = app.populate_form(101)
    assert "Modification" in res[0]
    assert res[2] == "RDV" # Mode
    assert res[6] == "Vannes" # Ville

def test_handle_table_actions(mocker):
    """Teste les boutons Modifier / Supprimer."""
    rows = [{'id': 101}, {'id': 102}]
    mock_ctx = mocker.patch('app.ctx')
    
    # Reset
    mock_ctx.triggered_id = "btn-reset"
    url, edit_id, alert, refresh = app.handle_table_actions(1, 0, 0, [], rows)
    assert url == "/input"

    # Modifier
    mock_ctx.triggered_id = "btn-edit-mode"
    url, edit_id, alert, refresh = app.handle_table_actions(1, 0, 0, [0], rows)
    assert url == "/input"
    assert edit_id == 101

    # Supprimer
    mock_ctx.triggered_id = "btn-delete"
    mocker.patch('app.delete_entretien_db', return_value=(True, "Supprimé"))
    url, edit_id, alert, refresh = app.handle_table_actions(0, 1, 0, [0], rows)
    assert "Supprimé" in alert.children

def test_save_form_data_validation(mocker):
    """Teste la validation du formulaire."""
    # Erreur
    res, trigger = app.save_form_data(1, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None)
    assert "Champs obligatoires manquants" in res.children
    
    # Succès
    mocker.patch('app.save_entretien_db', return_value=(True, "OK"))
    res, trigger = app.save_form_data(1, None, "2023-01-01", "RDV", "15-30 min", "Homme", "-18 ans", "Vannes", 0, "Célibataire", "Tradi", "Soi", "Ouvrier", "RSA", "1a", "CAF", "Dem", "Sol")
    assert "OK" in res.children

def test_update_dashboard_complete(mocker, mock_db_data):
    """Teste le dashboard."""
    # On doit simuler des données 'finales' (avec Annee, Mois, etc.)
    df_processed = mock_db_data.copy()
    df_processed.rename(columns={'commune': 'Ville', 'partenaire': 'Partenaire'}, inplace=True)
    df_processed['Annee'] = '2023'
    df_processed['Mois'] = '2023-01'
    df_processed['Mode_Lib'] = 'RDV'
    df_processed['Age_Lib'] = '26-40'
    df_processed['Sexe_Lib'] = 'Femme'
    df_processed['Sit_Lib'] = 'Marié'
    df_processed['Prof_Lib'] = 'Employé'
    
    app.df_global = df_processed
    mock_ctx = mocker.patch('app.ctx')
    
    mock_ctx.triggered_id = "btn-act"
    kpi, graphs, c1, c2, c3 = app.update_dashboard('2023', 0, 0, 0, 0)
    assert c1 == "primary"
    
    mock_ctx.triggered_id = "btn-cli"
    kpi, graphs, c1, c2, c3 = app.update_dashboard('2023', 0, 0, 0, 0)
    assert c2 == "primary"



def test_error_cases(mocker):
    """
    Ce test simule des erreurs pour valider les blocs 'except' 
    et augmenter la couverture de code (Coverage).
    """
    # Cas 1 : Plantage lors du chargement des données
    # On simule que get_db_connection renvoie une erreur
    mocker.patch('app.get_db_connection', side_effect=Exception("Connexion impossible"))
    df = app.load_data_from_db()
    assert df.empty # Doit retourner un dataframe vide en cas d'erreur
    
    # Cas 2 : Plantage lors de la suppression
    # On mock une connexion, mais le curseur plante
    mock_conn = MagicMock()
    mock_conn.cursor.side_effect = Exception("Erreur SQL Delete")
    mocker.patch('app.get_db_connection', return_value=mock_conn)
    
    success, msg = app.delete_entretien_db(1)
    assert success is False
    assert "Erreur SQL Delete" in msg
    mock_conn.rollback.assert_called() # Vérifie que le rollback (annulation) est bien appelé

    mock_conn.cursor.side_effect = Exception("Erreur SQL Save")
    success, msg = app.save_entretien_db({}, update_id=None)
    assert success is False
    assert "Erreur SQL Save" in msg