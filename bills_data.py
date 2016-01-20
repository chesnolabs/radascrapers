#!/usr/bin/env python3
# coding:utf-8

import os
import re
from pyquery import PyQuery as pq
from dateutil import parser
import time
import datetime
import pytz
import json
from csv import writer
import requests

from rada import rada
from settings import OUTPUT_FOLDER, PERSON_IDS_FILE

START_URL = 'http://w1.c1.rada.gov.ua/pls/zweb2/'

LIST_ELEMENT = 'ul#gol_v'
ELEMENT_LINK_TAG = 'li a'
INITIATOR_SELECTOR = 'div.zp-info dt:contains'\
                    '("єкт права законодавчої ініціативи:")'
AUTHORS_SELECTOR = 'dd#authors li'
CONVOCATION_NUMBER = re.compile("\(VI?I?I? скликання\)")
MAIN_COMMITTEE_SELECTOR = 'div.zp-info dt:contains("Головний комітет:")'
OTHERS_COMMITTEES_SELECTOR = 'div.zp-info dt:contains("Інші комітети:")'
LAST_STATUS_SELECTOR = 'div#flow_tab th:eq(1)'
LAST_STAGE_SELECTOR = 'div#flow_tab td:eq(1)'
BILL_DOCS_SELECTOR = 'div.zp-info dt:contains("Текст законопроекту")'
FLOW_DOCS_SELECTOR = 'div.zp-info dt:contains("язані із роботою")'
FLOW_LINK_SELECTOR = 'div.tabs_block li:last a'
FLOW_LINK_TEMPLATE = 'http://w1.c1.rada.gov.ua'
COMMITEES_TABLE_SELECTOR = 'div#kom_processing_tab table:eq(0)'
COMMITEES_ROW_SELECTOR = 'tr:gt(0)'
COMMITEES_CELLS_SELECTOR = 'td'
VOTING_DATES_SELECTOR = 'div.fr_data'

DATE_RE = re.compile("(?P<date>\d{2}.\d{2}.\d{4})")

SLEEP_TIME = 0.3
LONG_SLEEP = 180
UPDATE_LIMIT = 3 * 3600

NUMBER_OF_ATTEMPTS = 3


ACT_TYPES = {
        "Проект Закону": 'закон',
        "Проект Постанови": 'постанова',
}
ACT_TYPE_OTHER = "інше"

DUMP_FILE = OUTPUT_FOLDER + 'bill_cards.json'
GENERAL_INFO_FILE = OUTPUT_FOLDER + "bills.csv"
COMMITTEES_LIST_FILE = OUTPUT_FOLDER + "committees_list.csv"
UNIQUE_DOCS_FILE = OUTPUT_FOLDER + "docs_list.csv"

GENERAL_INFO_HEADERS = ["number", "title", "URL", "type", "filing_date",
                        "status", "initiator_type", "initiators", "committee",
                        "committees", "convocation", "last_updated"]
COMMITTEES_LIST_HEADERS = ["committee", 'convocation']
UNIQUE_DOCS_HEADER = ["name"]


def dump_dict():
    with open(DUMP_FILE, 'w') as fp:
        json.dump(bills_dict, fp)


def pq_opener(url, **kwargs):
    time.sleep(SLEEP_TIME)
    try:
        r = requests.get(url)
        return r.text
    except Exception:
        global flag
        flag = True
        dump_dict()
        print("An error occurred. The dictionary has been dumped.")


def change_date_format(s):
    parts = s.split(".")
    return parts[2] + '-' + parts[1] + '-' + parts[0]


def un_standard_names(s):
    keys = list(ids.keys())
    return_list = list()
    for k in keys:
        if k in s:
            return_list.append(k)
    return return_list


def write_general_info(key):
    b = bills_dict[key]
    authors_str = map(lambda x: str(x), b['authors']['id'])
    output_row = [key, b["title"], b['link'], b['type'],
                  change_date_format(b['filing_date']), b['last_status'],
                  b['initiator_type'], ','.join(authors_str),
                  b['main_committee'], "|".join(b['others_committees']),
                  b['convocation'], b['last_updated']]
    general_info_writer.writerow(output_row)


def append_committee(key):
    global committees_dict
    bill = bills_dict[key]
    if not (bill['convocation'] in committees_dict.keys()):
        committees_dict[bill['convocation']] = []
    committees_dict[bill['convocation']] = list(set(committees_dict
                                                    [bill['convocation']] +
                                                    bill['others_committees'] +
                                                    [bill['main_committee']]))


def write_committees_list():
    committees_list_csv = open(COMMITTEES_LIST_FILE, 'w')
    committees_list_writer = writer(committees_list_csv)
    committees_list_writer.writerow(COMMITTEES_LIST_HEADERS)
    for k in committees_dict.keys():
        for com in committees_dict[k]:
            committees_list_writer.writerow([com, k])
    committees_list_csv.close()


def committee_strip(s):
    return s.replace("Комітет Верховної Ради України", "Комітет")


def write_docs_list():
    docs_list_csv = open(UNIQUE_DOCS_FILE, 'w')
    docs_list_writer = writer(docs_list_csv)
    docs_list_writer.writerow(UNIQUE_DOCS_HEADER)
    for doc in unique_docs:
        docs_list_writer.writerow([doc])
    docs_list_csv.close()


def get_docs(x):
    text = pq(x).text()
    date_matched = DATE_RE.search(text)
    if date_matched is not None:
        date = change_date_format(date_matched.group("date"))
    else:
        date = ""
    name = DATE_RE.sub('', text).strip()
    link = START_URL + pq(x).attr("href")
    return name, date, link


def get_bills_features(link):
        # print(link)
        try:
            page = pq(url=link, opener=pq_opener)
        except Exception:
            return {}
        features = {}
        features['initiator'] = page(INITIATOR_SELECTOR).next().text()
        features['main_committee'] = committee_strip(page(
                                        MAIN_COMMITTEE_SELECTOR
                                        ).next().text())
        other_committees_raw = str(
            page(OTHERS_COMMITTEES_SELECTOR).next().children()
            ).replace('</li>', '').split('<li>')[1:]
        features['others_committees'] = list(map(
            committee_strip, other_committees_raw))
        features['last_status'] = page(LAST_STATUS_SELECTOR).text()
        last_stage_line = page(LAST_STAGE_SELECTOR).text()
        last_updated_matched = DATE_RE.search(last_stage_line)
        if last_updated_matched:
            last_updated = change_date_format(
                                last_updated_matched.group('date'))
        else:
            last_updated = ''
        last_stage = last_stage_line.split("(")[0].strip()
        features['last_stage'] = last_stage
        features['last_updated'] = last_updated
        features['convocation'] = "Верховна Рада 8"
        features['bill_docs'] = {}
        bill_docs = page(BILL_DOCS_SELECTOR).next()('li a')
        docs_list = list(map(get_docs, bill_docs))
        features['bill_docs']['name'] = list(map(lambda x: x[0], docs_list))
        features['bill_docs']['date'] = list(map(lambda x: x[1], docs_list))
        features['bill_docs']['link'] = list(map(lambda x: x[2], docs_list))
        features['flow_docs'] = {}
        flow_docs = page(FLOW_DOCS_SELECTOR).next()('li a:empty')
        if flow_docs.text() != "":
            docs_list = list(map(get_docs, flow_docs))
            features['flow_docs']['name'] = list(map(lambda x: x[0],
                                                     docs_list))
            features['flow_docs']['date'] = list(map(lambda x: x[1],
                                                     docs_list))
            features['flow_docs']['link'] = list(map(lambda x: x[2],
                                                     docs_list))
        authors = page(AUTHORS_SELECTOR).text()
        if "Президент" in authors:
            features['initiator_type'] = "Президент України"
        elif "Міністрів" in authors:
            features['initiator_type'] = "Кабінет Міністрів України"
        else:
            features['initiator_type'] = "Народний депутат України"
        features['authors'] = {}
        if CONVOCATION_NUMBER.search(authors):
            authors = CONVOCATION_NUMBER.split(authors)
            authors = authors[0:len(authors)-1]
            authors = list(map(lambda s: s.strip(), authors))
            features['authors']['name'] = authors
            features['authors']['id'] = list(map(lambda s: ids[s], authors))
        else:
            authors = un_standard_names(authors)
            features['authors']['name'] = authors
            features['authors']['id'] = list(map(lambda s: ids[s], authors))
        flow_link = FLOW_LINK_TEMPLATE + page(FLOW_LINK_SELECTOR).attr('href')
        try:
            flow_page = pq(url=flow_link, opener=pq_opener)
        except Exception:
            return {}
        dates_times = flow_page(VOTING_DATES_SELECTOR).text().split()
        dates = dates_times[0::2]
        times = dates_times[1::2]
        features['voting_ids'] = list(
            map(lambda d, t: int(parser.parse(
                d + ' ' + t, tzinfos=datetime.timedelta(0),
                dayfirst=True)
                .replace(tzinfo=pytz.utc).timestamp()), dates, times))
        commitees_flow = {}
        commitees = page(COMMITEES_TABLE_SELECTOR)
        commitees = pq(commitees)
        commitees = commitees(COMMITEES_ROW_SELECTOR)
        for c in commitees:
            c = pq(c)
            cells = c(COMMITEES_CELLS_SELECTOR)
            cells_list = list()
            for cell in cells:
                cell = pq(cell)
                cells_list.append(cell.text())
            commitees_flow[cells_list[0]] = {}
            commitees_flow[cells_list[0]]['sent_date'] = cells_list[1]
            commitees_flow[cells_list[0]]['received_date'] = cells_list[2]
        features['committees_flow'] = commitees_flow
        return features


def download_bill(key):
    for act_type in ACT_TYPES:
        if bill_list[key][2].startswith(act_type):
            bill_list[key].append(ACT_TYPES[act_type])
    if len(bill_list[key]) == 3:
        bill_list[key].append(ACT_TYPE_OTHER)
    bd = {}
    bd["link"] = bill_list[key][0]
    bd["filing_date"] = bill_list[key][1]
    bd["title"] = bill_list[key][2]
    bd["type"] = bill_list[key][3]
    bd["update_time"] = int(datetime.datetime.now().strftime("%s"))
    bd.update(get_bills_features(bd["link"]))
    return bd

# open json with MP ids
with open(PERSON_IDS_FILE) as json_data:
        ids = json.load(json_data)
        json_data.close()


# this loop executes till all bills are downloaded
flag = True
while flag:
    unique_docs = []
    flag = False
    # open output .csv file
    general_info_csv = open(GENERAL_INFO_FILE, 'w')
    general_info_writer = writer(general_info_csv)
    general_info_writer.writerow(GENERAL_INFO_HEADERS)
    committees_dict = {}
    if os.path.isfile(DUMP_FILE):
        with open(DUMP_FILE) as json_dump:
            bills_dict = json.load(json_dump)
            json_dump.close()
    else:
        bills_dict = {}
    # print("Downloading bills...")
    bills_downloaded = False
    attempt = 1
    while not bills_downloaded and attempt <= NUMBER_OF_ATTEMPTS:
        try:
            bill_list = rada.list_bills()
            bills_downloaded = True
        except Exception:
            print("Cannot download bills list. Taking a looong rest...")
            bills_downloaded = False
            attempt += 1
            time.sleep(LONG_SLEEP * 5)
    if not bills_downloaded:
        break
    keys = list(bill_list.keys())
    for i in range(len(keys)):
        # print(str(i + 1) + " from " + str(len(keys)))
        key = keys[i]
        if key in bills_dict.keys():
            now = int(datetime.datetime.now().strftime("%s"))
            if (now - bills_dict[key]['update_time']) > UPDATE_LIMIT:
                bills_dict[key] = download_bill(key)
        else:
            bills_dict[key] = download_bill(key)
        if flag:
            print("Something got wrong, taking a rest...")
            time.sleep(LONG_SLEEP)
            break
        if bills_dict[key]['bill_docs'] != {}:
            unique_docs = list(set(unique_docs +
                                   bills_dict[key]['bill_docs']['name']))
        if bills_dict[key]['flow_docs'] != {}:
            unique_docs = list(set(unique_docs +
                                   bills_dict[key]['flow_docs']['name']))
        write_general_info(key)
        append_committee(key)
    general_info_csv.close()


if bills_downloaded:
    dump_dict()
    write_committees_list()
    write_docs_list()
