import pandas as pd
import numpy as np
import json
import psycopg2

CHEMIN_DONNEES = json.load(open('config.json', 'r'))['DATA_FILE_PATH']
MOIS = ["Jan", "Fev", "Mar", "Avr", "Mai", "Juin", "Juil", "Aoû", "Sep", "Oct", "Nov", "Déc"]
ANNEE_COURANTE = "2025"

MAPPING_DATES = {
    "Jan": f"{ANNEE_COURANTE}-01-01", "Fev": f"{ANNEE_COURANTE}-02-01", "Mar": f"{ANNEE_COURANTE}-03-01",
    "Avr": f"{ANNEE_COURANTE}-04-01", "Mai": f"{ANNEE_COURANTE}-05-01", "Juin": f"{ANNEE_COURANTE}-06-01",
    "Juil": f"{ANNEE_COURANTE}-07-01", "Aoû": f"{ANNEE_COURANTE}-08-01", "Sep": f"{ANNEE_COURANTE}-09-01",
    "Oct": f"{ANNEE_COURANTE}-10-01", "Nov": f"{ANNEE_COURANTE}-11-01", "Déc": f"{ANNEE_COURANTE}-12-01"
}

# --- LISTE DES VARIANTES DE NOMS DE COLONNES 
COLS_ALIAS = {
    "MODE": ["Mode"],
    "DUREE": ["Durée", "Duree"],
    "SEXE": ["Sexe"],
    "AGE": ["Age", "Âge"],
    "VIENT_PR": ["Vient pr", "Vient pour", "Vient"], 
    "SIT_FAM": ["Sit° Fam", "Sit Fam", "Situation Familiale"],
    "ENFANT": ["Enfts", "Enfants", "Enf."],
    "MODELE_FAM": ["Modèle fam.", "Modele fam", "Modèle Familial"],
    "PROFESSION": ["Prof°", "Prof", "Profession"], 
    "RESS": ["Ress. 1", "Ressources", "Ress 1"], 
    "ORIGINE": ["Origine"],
    "COMMUNE": ["Domicile", "Commune", "Ville"],
    "PARTENAIRE": ["Partenaire"]
}

MAPPING_VALEURS = {
    # MODE
    "RDV": 1, "Sans RDV": 2, "Tel": 3, "Téléphonique": 3, "Courrier": 4, "Mail": 5,
    # DUREE
    "- de 15 min": 1, "<15min": 1, "-5min": 1, "15 à 30 min": 2, "15/30min": 2, 
    "30 à 45 min": 3, "45 à 60 min": 4, "0/45 min": 4, "5/60min": 4, "+ de 60 min": 5, "+60min": 5, ">30min": 5,
    # SEXE
    "Homme": 1, "Femme": 2, "Couple": 3, "Professionnel": 4, "Pro": 4,
    # AGE
    "-18 ans": 1, "-8ans": 1, "18/5ans": 2, "18-25 ans": 2, "26-40 ans": 3, "26/40ans": 3, 
    "41-60 ans": 4, "1/60ans": 4, "+ 60 ans": 5, "+60ans": 5,
    # VIENT_PR
    "Soi": 1, "Conjoint": 2, "Parent": 3, "Enfant": 4, "Persmor": 5, "Autre": 6,
    # SIT_FAM
    "Célib": "1", "Célibataire": "1", "Concubin": "2", "Pacsé": "3", "Marié": "4",
    "Séparé/divorcé": "5", "Sép /s mm toit": "5f", "Parisolé": "5e", "Veuf/ve": "6", "Non renseigné": "7", "nan": "7",
    # MODELE_FAM
    "Tradi": 1, "Famille traditionnelle": 1, "Monop": 2, "Famille monoparentale": 2, "Recomp": 3,
    # PROFESSION
    "Sco/étud": 1, "Scolaire": 1, "Pêch/agri": 2, "Chef ent": 3, "Libéral": 4, "Militaire": 5,
    "Employé": 6, "Ouvrier": 7, "Cadre": 8, "Retraité": 9, "Ddeur emploi": 10, "Sss prof°": 11, "Sans profession": 11,
    # RESS
    "Salaire": 1, "Revenus pro": 2, "Retraite/rév": 3, "Chômage": 4, "RSA": 5, "AAH": 6, "AAH/Invalidité": 6, "IJSS": 7,
    "Bourse": 8, "Sans revenu": 9, "Autre": 10,
    # ORIGINE
    "Com Bouche à oreille": "1a", "Bouche à oreille": "1a", "Com Internet": "1b", "Internet": "1b", "Com Presse": "1c",
    "Déjà venu Suite": "2a", "Déjà venu Autre": "2b",
    "Pro droit Tribunaux": "3a", "Pro droit Police": "3b", "Pro droit": "3c",
    "Admin CAF": "4a", "Admin DIRECCTE": "4b", "Admin MFS": "4c", "Admin Mairie": "4d", "Admin Autre": "4e",
    "Santé AS": "5a", "Santé Educ": "5b", "Santé Pro": "5c", "Santé Jeunesse": "5d", "Santé RIPAM": "5e",
    "Asso France Victimes": "6a", "Asso Conso": "6b", "Asso ADIL": "6c", "Asso UDAF": "6d", "Asso accès droit": "6e", "Asso Autre": "6f",
    "Privé PJ": "7a", "Privé Autre": "7b", "Action coll": "8", "3949 NUAD": "9"
}

class Read_xl:
    def __init__(self):
        self.feuilles = pd.read_excel(CHEMIN_DONNEES, sheet_name=None, header=None) 

    def main(self):
        print("--- DÉBUT ---")
        DB_CONFIG = json.load(open('config.json', 'r', encoding='utf-8'))["POSTGRES"]
        conn = psycopg2.connect(**DB_CONFIG)
        
        # --- NETTOYAGE (Optionnel : à commenter si vous ne voulez pas vider la base) ---
        try:
            cur = conn.cursor()
            cur.execute("TRUNCATE TABLE entretien, demande, solution RESTART IDENTITY CASCADE;")
            conn.commit()
            print(">> Base de données vidée pour import propre.")
        except Exception as e:
            conn.rollback()
            print(f"Erreur nettoyage : {e}")
        # -----------------------------------------------------------------------------

        try:
            for mois in MOIS:
                if mois not in self.feuilles: continue
                
                print(f"Traitement : {mois}")
                df = self.extraction_dataframe(self.feuilles[mois])
                if df.empty: continue
                df = df.astype(str)

                for index, ligne in df.iterrows():
                    self.inserer_complet(conn, ligne, mois)
                
                print(f"Mois {mois} terminé.")

        except Exception as e:
            print(f"ERREUR CRITIQUE : {e}")
        finally:
            conn.close()
            print("--- FIN ---")

    def extraction_dataframe(self, df: pd.DataFrame):
        tabs_index = df.index[df.iloc[:, 1] == "Mode"].tolist()
        if len(tabs_index) < 1: return pd.DataFrame()
        fin = tabs_index[1] if len(tabs_index) > 1 else None
        
        donnes = df[tabs_index[0]+1 : fin].copy()
        donnes.columns = df.iloc[tabs_index[0]] 
        donnes.columns = donnes.columns.str.strip() # Enlève les espaces invisibles avant/après
        return donnes

    def get_col_value(self, ligne, cle_alias):
        """ Cherche la valeur dans la ligne en essayant plusieurs noms de colonnes possibles """
        possibilites = COLS_ALIAS.get(cle_alias, [])
        for col_name in possibilites:
            if col_name in ligne:
                return ligne[col_name]
        return 'NULL' # Si aucune colonne trouvée

    def inserer_complet(self, conn, ligne, mois_nom):
        cur = conn.cursor()
        try:
            date_sql = MAPPING_DATES.get(mois_nom, f"{ANNEE_COURANTE}-01-01")

            # --- Utilisation de la fonction flexible pour récupérer les valeurs ---
            sit_fam_clean = self.clean_str(self.get_col_value(ligne, "SIT_FAM"), max_len=2)
            origine_clean = self.clean_str(self.get_col_value(ligne, "ORIGINE"), max_len=2)

            valeurs = {
                "MODE": self.clean_int(self.get_col_value(ligne, "MODE")),
                "DUREE": self.clean_int(self.get_col_value(ligne, "DUREE")),
                "SEXE": self.clean_int(self.get_col_value(ligne, "SEXE")),
                "AGE": self.clean_int(self.get_col_value(ligne, "AGE")),
                "VIENT_PR": self.clean_int(self.get_col_value(ligne, "VIENT_PR")),
                "SIT_FAM": sit_fam_clean,
                "ENFANT": self.clean_int(self.get_col_value(ligne, "ENFANT")),
                "MODELE_FAM": self.clean_int(self.get_col_value(ligne, "MODELE_FAM")),
                "PROFESSION": self.clean_int(self.get_col_value(ligne, "PROFESSION")),
                "RESS": self.clean_int(self.get_col_value(ligne, "RESS")),
                "ORIGINE": origine_clean,
                "COMMUNE": self.clean_str(self.get_col_value(ligne, "COMMUNE")),
                "PARTENAIRE": self.clean_str(self.get_col_value(ligne, "PARTENAIRE"))
            }

            if valeurs["MODE"] == "NULL" and valeurs["SEXE"] == "NULL": return
            if valeurs["ENFANT"] == "NULL": valeurs["ENFANT"] = "0"

            query_ent = f"""
                INSERT INTO entretien 
                (date_ent, mode, duree, sexe, age, vient_pr, 
                 sit_fam, enfant, modele_fam, profession, ress, origine, commune, partenaire)
                VALUES 
                ('{date_sql}', {valeurs['MODE']}, {valeurs['DUREE']}, {valeurs['SEXE']}, {valeurs['AGE']}, {valeurs['VIENT_PR']},
                 {valeurs['SIT_FAM']}, {valeurs['ENFANT']}, {valeurs['MODELE_FAM']}, {valeurs['PROFESSION']}, {valeurs['RESS']}, 
                 {valeurs['ORIGINE']}, {valeurs['COMMUNE']}, {valeurs['PARTENAIRE']})
                RETURNING num;
            """
            cur.execute(query_ent)
            num_entretien = cur.fetchone()[0]

            # DEMANDES (Colonnes Dem.1, Dem.2, Dem.3)
            pos_d = 1
            for col_dem in ['Dem.1', 'Dem.2', 'Dem.3']:
                if col_dem in ligne:
                    val = str(ligne[col_dem]).strip()
                    if val not in ['nan', '', 'None', 'NULL']:
                        cur.execute(f"INSERT INTO demande (num, pos, nature) VALUES ({num_entretien}, {pos_d}, '{val.replace("'", "''")}')")
                        pos_d += 1

            # SOLUTIONS (Colonnes Sol.1, Sol.2, Sol.3)
            pos_s = 1
            for col_sol in ['Sol.1', 'Sol.2', 'Sol.3']:
                if col_sol in ligne:
                    val = str(ligne[col_sol]).strip()
                    if val not in ['nan', '', 'None', 'NULL']:
                        cur.execute(f"INSERT INTO solution (num, pos, nature) VALUES ({num_entretien}, {pos_s}, '{val.replace("'", "''")}')")
                        pos_s += 1

            conn.commit()

        except Exception as e:
            conn.rollback()
            # Pour debug : Affiche quelle colonne pose problème
            print(f" Erreur ligne (Mois {mois_nom}) : {e}")

    def clean_int(self, val):
        val = str(val).strip()
        if val in ['nan', 'None', '', 'NULL']: return 'NULL'
        if val in MAPPING_VALEURS: return str(MAPPING_VALEURS[val])
        return val if val.isdigit() else 'NULL'

    def clean_str(self, val, max_len=None):
        val = str(val).strip()
        if val in ['nan', 'None', '', 'NULL']: return 'NULL'
        
        if val in MAPPING_VALEURS: 
            return f"'{MAPPING_VALEURS[val]}'"
        
        if max_len and len(val) > max_len:
            val = val[:max_len]
            
        return f"'{val.replace("'", "''")}'"

if __name__ == "__main__":
    Read_xl().main()