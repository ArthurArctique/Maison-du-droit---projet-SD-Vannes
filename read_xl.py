import pandas as pd
import json

CHEMIN_DONNEES = json.load(open('config.json','r'))['DATA_FILE_PATH']
SUPPR_FEUILLES = ['N°',"Total quartiers"]
COLLS_NON_CAT = ["Tot.Dem.","Tot.Sol","N°"]
MOIS = ["Jan","Fev","Mar","Avr","Mai","Juin","Juil","Aoû","Sep","Oct","Nov","Déc"]


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
            print(mois)
            self.division_dataframes(feuille_df)

    def division_dataframes(self,df:pd.DataFrame):
        tabs_index = df.index[df.iloc[:, 1] == "Mode"].tolist()
        print(tabs_index)
        donnes_brut = df[tabs_index[0]+1:tabs_index[1]]
        donnes_brut.columns = df.iloc[tabs_index[0]]
        donnes_brut = donnes_brut.iloc[:,:donnes_brut.columns.get_loc("Domicile")+1]

        sec_part = df[tabs_index[1]+2:]
        sec_part.columns = df.iloc[tabs_index[1]]
        sec_part = sec_part.iloc[:,:sec_part.columns.get_loc("Domicile")].drop(columns=COLLS_NON_CAT)

    def mise_a_jour_carte(self,df):
        pass

Read_xl().main()