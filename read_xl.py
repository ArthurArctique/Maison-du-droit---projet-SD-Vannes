import pandas as pd
import numpy as np
import json
import sqlite3

CHEMIN_DONNEES = json.load(open('config.json','r'))['DATA_FILE_PATH']
SUPPR_FEUILLES = ['N°',"Total quartiers"]
COLLS_NON_CAT = ["Tot.Dem.","Tot.Sol","N°"]
MOIS = ["Jan","Fev","Mar","Avr","Mai","Juin","Juil","Aoû","Sep","Oct","Nov","Déc"]
CARTE_BDD = json.load(open('carte_bdd.json','r'))


class Read_xl:
    def __init__(self,path=CHEMIN_DONNEES):
        self.path = path
        self.feuilles = pd.read_excel(CHEMIN_DONNEES, sheet_name=None,header=None) # Dictionnaire où chaque feuille est un dataframe (clé : nom de feuille valeur : dataframe)
        self.carte = dict()
    
    def main(self):
        for mois in MOIS:
            if mois in SUPPR_FEUILLES:
                continue
            feuille_df = self.feuilles[mois]
            
            df = self.extraction_dataframe(feuille_df).astype(str).replace(self.carte)

            self.ajout_bdd_sqlite(df,mois)

    def extraction_dataframe(self,df:pd.DataFrame):
        tabs_index = df.index[df.iloc[:, 1] == "Mode"].tolist()

        donnes_brut = df[tabs_index[0]+1:tabs_index[1]]
        donnes_brut.columns = df.iloc[tabs_index[0]]
        donnes_brut = donnes_brut.iloc[:,:donnes_brut.columns.get_loc("Domicile")+1]

        sec_part = df[tabs_index[1]+2:]
        sec_part.columns = df.iloc[tabs_index[1]]
        sec_part = sec_part.iloc[:,:sec_part.columns.get_loc("Domicile")].drop(columns=COLLS_NON_CAT)
        

        self.mise_a_jour_carte(sec_part)
        return donnes_brut

    def mise_a_jour_carte(self,df):
        for col in df.columns:
            self.carte[col] = dict()
            for line in df[col]:
                if type(line) not in [int,float,np.nan]:
                    splt = line.split('.') if "." in line[:round(len(line)/2)] else line.split(' ')
                    index = splt[0]
                    self.carte[col][index] = line.replace(index,'').replace('.','').strip()
        self.carte['Dem.2'] = self.carte['Dem.3'] = self.carte['Dem.1']
        self.carte['Sol.2'] = self.carte['Sol.3'] = self.carte['Sol.1']
    
    def ajout_bdd_sqlite(self,df,mois):
        conn = sqlite3.connect("../database.db")
        cur = conn.cursor()

        val_bdd = list(CARTE_BDD["ENTRETIEN"].values()) + ['DATE_ENT']
        val_xl = list(CARTE_BDD["ENTRETIEN"].keys()) 

        for index, ligne in df.iterrows():
            vals_xl,vals_bdd = ",".join([f'"{ligne[val]}"' for val in val_xl]),",".join([f'"{val}"' for val in val_bdd])
            if vals_xl.split(',')[0] == '"nan"':
                continue
            print(vals_xl.split(',')[0])
            cur.execute(
                f"""
                INSERT INTO entretien ({vals_bdd}) 
                VALUES ({vals_xl},"{mois}");
                """
            )
            print('passé')
    

        conn.commit()
        conn.close()

Read_xl().main()