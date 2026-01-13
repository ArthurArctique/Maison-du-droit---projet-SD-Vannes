import pandas as pd
import json
import psycopg2
import re


CHEMIN_DONNEES = json.load(open('config.json', 'r', encoding='utf-8'))['DATA_FILE_PATH']
SUPPR_FEUILLES = ['N°', "Total quartiers"]
COLLS_NON_CAT = ["Tot.Dem.", "Tot.Sol", "N°"]
MOIS = ["Jan", "Fev", "Mar", "Avr", "Mai", "Juin", "Juil", "Aoû", "Sep", "Oct", "Nov", "Déc"]
CARTE_BDD = json.load(open('carte_bdd.json', 'r', encoding='utf-8'))


class Read_xl:

    def __init__(self, path=CHEMIN_DONNEES):
        self.path = path
        self.feuilles = pd.read_excel(self.path, sheet_name=None, header=None)
        self.carte = {}
    def main(self):
        for mois in MOIS:
            if mois in SUPPR_FEUILLES:
                continue

            feuille_df = self.feuilles[mois]
            df = self.extraction_dataframe(feuille_df)

            self.ajout_bdd_postgres(df, mois)
    def extraction_dataframe(self, df):

        tabs_index = df.index[df.iloc[:, 1] == "Mode"].tolist()

        donnees = df[tabs_index[0] + 1:tabs_index[1]]
        donnees.columns = df.iloc[tabs_index[0]]
        donnees = donnees.iloc[:, :donnees.columns.get_loc("Domicile") + 1]

        sec_part = df[tabs_index[1] + 2:]
        sec_part.columns = df.iloc[tabs_index[1]]
        sec_part = sec_part.iloc[:, :sec_part.columns.get_loc("Domicile")].drop(columns=COLLS_NON_CAT)

        self.construire_carte(sec_part)
        return donnees
    def construire_carte(self, df):
        for col in df.columns:
            self.carte[col] = {}
            for val in df[col]:
                if isinstance(val, str):
                    splt = val.split('.') if '.' in val[:len(val)//2] else val.split(' ')
                    code = splt[0].strip()
                    lib = val.replace(code, '').replace('.', '').strip()
                    if re.fullmatch(r"\d+", code):
                        self.carte[col][code] = lib

        self.carte['Dem.2'] = self.carte['Dem.3'] = self.carte['Dem.1']
        self.carte['Sol.2'] = self.carte['Sol.3'] = self.carte['Sol.1']

    
    def convertir_valeur(self, col, valeur):
        """
        Retourne STRICTEMENT :
        - un entier (str numérique)
        - ou 'NULL'
        """

        if valeur is None:
            return 'NULL'

        valeur = str(valeur).strip()

        if valeur.lower() == 'nan':
            return 'NULL'

        if col in self.carte:
            for code, lib in self.carte[col].items():
                if lib == valeur:
                    return code

        # entier pur uniquement
        if re.fullmatch(r"\d+", valeur):
            return valeur

        # tout le reste (5a, Tel, 1/60ans, etc.)
        return 'NULL'

    
    def ajout_bdd_postgres(self, df, mois):

        DB_CONFIG = json.load(open('config.json', 'r', encoding='utf-8'))["POSTGRES"]
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Colonnes BDD (NUM exclu)
        colonnes_bdd = [
            v for v in CARTE_BDD["ENTRETIEN"].values()
            if v != "NUM"
        ] + ["DATE_ENT"]

        colonnes_xl = [
            k for k, v in CARTE_BDD["ENTRETIEN"].items()
            if v != "NUM"
        ]

        cols_sql = ",".join([f'"{c}"' for c in colonnes_bdd])

        for _, ligne in df.iterrows():

            valeurs = [
                self.convertir_valeur(col, ligne[col])
                for col in colonnes_xl
            ]

            #  Sécurité ultime : aucune valeur non numérique
            if any(v not in ('NULL',) and not re.fullmatch(r"\d+", v) for v in valeurs):
                raise ValueError(f"Valeur invalide détectée : {valeurs}")

            date_ent = f"2025-{MOIS.index(mois)+1:02d}-01"
            vals_sql = ",".join(valeurs)

            sql = f"""
                INSERT INTO "ENTRETIEN" ({cols_sql})
                VALUES ({vals_sql}, '{date_ent}');
            """

            print(sql)
            cur.execute(sql)

        conn.commit()
        conn.close()


Read_xl().main()
