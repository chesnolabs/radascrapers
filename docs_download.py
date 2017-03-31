import json
import urllib.request
import time
from settings import OUTPUT_FOLDER

BILLS_FILE = OUTPUT_FOLDER + 'bill_cards.json'

FILTERS = {
    'main_committee': "Комітет з питань Регламенту та організації роботи Верховної Ради України"
    }

DOCS_TO_DOWNLOAD = ["Пояснювальна записка", "Порівняльна таблиця"]
NAME_PREFIXES = ["poyasn", "porivn"]

DOCS_FOLDER = OUTPUT_FOLDER + 'docs/reglament'

SLEEP_TIME = 0.5


def filter_by(raw_dict, parameters):
    if type(parameters) is dict:
        bools = list(map(filter_by, [raw_dict[k] for k in parameters.keys()], [parameters[k] for k in parameters.keys()]))
        return sum(bools) == len(bools)
    else:
        return raw_dict == parameters

with open(BILLS_FILE) as bills_file:
        bills_dict = json.load(bills_file)
        bills_file.close()

bills_dict = {k: v for k, v in bills_dict.items() if filter_by(v, FILTERS)}

for k in bills_dict.keys():
    print(k)
    for doc_number in range(len(DOCS_TO_DOWNLOAD)):
        doc = DOCS_TO_DOWNLOAD[doc_number]
        if doc in bills_dict[k]['bill_docs']['name']:
            index = bills_dict[k]['bill_docs']['name'].index(doc)
            link = bills_dict[k]['bill_docs']['link'][index]
            filename = DOCS_FOLDER + "/" + k + "_" + NAME_PREFIXES[doc_number] + ".rtf"
            urllib.request.urlretrieve(link, filename)
            time.sleep(SLEEP_TIME)
