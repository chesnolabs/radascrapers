import json
import urllib.request
import time
import os
import re
from csv import writer
from pyquery import PyQuery as pq

OUTPUT_FOLDER = '../output/'
DOCS_FOLDER = OUTPUT_FOLDER + 'docs/'

BILLS_FILE = OUTPUT_FOLDER + 'bill_cards.json'
OUTPUT_FILE = OUTPUT_FOLDER + 'discusses.csv'
DOCS_TYPE = 'Пояснювальна записка'
INITIATOR_TYPES = ["кабмін"]

OUTPUT_HEADERS = ["number", "title", "social_partners", "civic_society"]

DISCUSS_SELECTOR = 'b:contains("Громадське обговорення")'
DISCUSS_SELECTOR_2 = 'b:contains("8.")'

FILENAME_PART = 'poyasn'
FOLDER = 'output/docs/'
EXTENSION = '.rtf'

SLEEP_TIME = 0.3

with open(BILLS_FILE) as bills_file:
        bills_dict = json.load(bills_file)
        bills_file.close()


def civic_discusses_paragraph(p, s=''):
    if "9." in pq(p).text() or (
      ("соціальних" in pq(p).text()) or ("партнерів" in pq(p).text())):
        return s
    elif pq(p).next() != None:
        return civic_discusses_paragraph(
                    pq(p).next(), s + " " + pq(p).text().strip())
    else:
        return civic_discusses_paragraph(
                    pq(p).parent(), s + " " + pq(p).text().strip())


def stakeholders_paragraph(p, s=''):
    if "6." in pq(p).text() or (
      ("Регіональний" in pq(p).text()) or ("аспект" in pq(p).text())):
        return s
    elif pq(p).next() != None:
        return stakeholders_paragraph(
                    pq(p).next(), s + " " + pq(p).text().strip())
    else:
        return stakeholders_paragraph(
                    pq(p).parent(), s + " " + pq(p).text().strip())


def social_partners_paragraph(p, s=''):
    if "10." in pq(p).text() or (
      ("регуляторного" in pq(p).text()) or
      ("впливу" in pq(p).text())):
        return s
    elif pq(p).next() != None:
        return social_partners_paragraph(
                    pq(p).next(), s + " " + pq(p).text().strip())
    else:
        return social_partners_paragraph(
                    pq(p).parent(), s + " " + pq(p).text().strip())

output_csv = open(OUTPUT_FILE, 'w')
output_csv_writer = writer(output_csv)
output_csv_writer.writerow(OUTPUT_HEADERS)

all_bills = 0
do_not_need_consults = 0

problematic_bills = []
for k in bills_dict.keys():
    if bills_dict[k]['initiator_type'] in INITIATOR_TYPES:
        print(k)
        all_bills += 1
        docs = bills_dict[k]['bill_docs']
        if DOCS_TYPE in docs['name']:
            number = docs['name'].index(DOCS_TYPE)
            link = docs['link'][number]
            filename = DOCS_FOLDER + k + '_' + FILENAME_PART + EXTENSION
            urllib.request.urlretrieve(link, filename)
            time.sleep(SLEEP_TIME)
            script = "unoconv -f html " + filename
            os.system("bash -c '%s'" % script)
            h_filename = filename.replace(".rtf", ".html")
            try:
                page = pq(filename=h_filename)
                civic_discusses = page('body').children().filter(
                    lambda i: ("Громадське" in pq(this).text()) and
                    ("обговорення" in pq(this).text()))
                if len(civic_discusses) > 0:
                    civic_discusses_results = civic_discusses_paragraph(
                                                civic_discusses)
                    if len(civic_discusses_results.split(
                                        "обговорення", maxsplit=1)) > 1:
                        civic_discusses_results = civic_discusses_results \
                            .split("обговорення", maxsplit=1)[1].strip()
                    civic_discusses_results = re.sub(r"\s+", ' ',
                                                     civic_discusses_results)
                else:
                    civic_discusses_results = ''
                social_partners = page('body').children().filter(
                    lambda i: ("соціальних" in pq(this).text()) and
                    ("партнерів" in pq(this).text()))
                if len(social_partners) > 0:
                    social_partners_results = social_partners_paragraph(
                                                    social_partners)
                    if len(social_partners_results.split(
                      "партнерів", maxsplit=1)) > 1:
                        social_partners_results = social_partners_results \
                            .split("партнерів", maxsplit=1)[1].strip()
                        social_partners_results = re.sub(
                                                    r"\s+", ' ',
                                                    social_partners_results)
                else:
                    social_partners_results = ''
            except Exception:
                problematic_bills.append(k)
                civic_discusses_results = ''
                social_partners_results = ''
            if "не потребує" in civic_discusses_results:
                do_not_need_consults += 1
            print(civic_discusses_results)
            print(social_partners_results)
            output_row = [k, bills_dict[k]['title'],
                          social_partners_results, civic_discusses_results]
            output_csv_writer.writerow(output_row)

output_csv.close()
print(problematic_bills)
print(str(do_not_need_consults) + " from " + str(all_bills))
