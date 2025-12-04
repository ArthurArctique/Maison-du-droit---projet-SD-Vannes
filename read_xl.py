import pandas as pd
import json

FILE_PATH = json.load(open('config.json','r'))['DATA_FILE_PATH']

sheets = pd.read_excel(FILE_PATH, sheet_name=None)

print(sheets)