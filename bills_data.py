#!/usr/bin/env python3
# coding:utf-8

import os
import re
import time
import datetime
import json
from csv import writer
import socket
from traceback import format_exc
import argparse
import logging as log

from pyquery import PyQuery as pq
from dateutil import parser
import pytz
import socks
import requests

from rada import rada
from settings import OUTPUT_FOLDER, PERSON_IDS_FILE, HTTP_CODES_OK

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
STAGE_SELECTOR = 'div#flow_tab tr:gt(0)'
BILL_DOCS_SELECTOR = 'div.zp-info dt:contains("Текст законопроекту")'
FLOW_DOCS_SELECTOR = 'div.zp-info dt:contains("язані із роботою")'
FLOW_LINK_SELECTOR = 'div.tabs_block li:last a'
FLOW_LINK_TEMPLATE = 'http://w1.c1.rada.gov.ua'
COMMITEES_TABLE_SELECTOR = 'div#kom_processing_tab table:eq(0)'
COMMITEES_ROW_SELECTOR = 'tr:gt(0)'
COMMITEES_CELLS_SELECTOR = 'td'
EDITION_SELECTOR = 'div.zp-info dt:contains("Редакція законопроекту")'
SPHERE_SELECTOR = 'div.zp-info dt:contains("Рубрика законопроекту")'

VOTING_DATES_SELECTOR = 'div.fr_data'

DATE_RE = re.compile("(?P<date>\d{2}.\d{2}.\d{4})")
COMMITTEE_HEAD_RE = re.compile('(.*[Є-ЯҐA-Z]\.)?(.*)')

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

argparser = argparse.ArgumentParser()
argparser.add_argument('-d', '--debug', action='store_true', help='debug mode')
args = argparser.parse_args()
log.basicConfig(
    format='%(levelname)s:%(message)s',
    level=(args.debug and log.DEBUG or log.WARNING))
log.debug('Debug mode active.')


def html_body_present(html):
    if pq(html)('body'):
        return True
    return False


def info_container_present(html):
    if pq(html)('body div.zp-info'):
        return True
    return False


def pq_opener(url, verifier=html_body_present, **kwargs):
    attempt = 0
    r = None
    while attempt < NUMBER_OF_ATTEMPTS:
        attempt += 1
        time.sleep(SLEEP_TIME*attempt**2)
        try:
            r = requests.get(url)
            if r.status_code in HTTP_CODES_OK and verifier(r.text):
                return r.text
        except Exception:
            log.warning(
                "Failed to download {} with status {}"
                .format(url, r and r.status_code or ""))
            log.warning(format_exc())
    global scrapper_failed
    scrapper_failed = True
    return None


def pq_opener_with_container_check(url, **kwargs):
    return pq_opener(url, verifier=info_container_present)


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
                  b['convocation'],
                  b['dates_updated'] and b['dates_updated'][0] or ""]
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


def committee_strip(committee_dd_text):
    committee_name = COMMITTEE_HEAD_RE.match(committee_dd_text)\
        .groups()[-1].strip()
    return committee_name.replace("Комітет Верховної Ради України", "Комітет")


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


def get_updates(x):
    x = pq(x)
    date = change_date_format(x('td:eq(0)').text())
    stage = x('td:eq(1)').text()
    return stage, date


def parse_date(d, t):
    combined_datetime = '{} {}'.format(d, t)
    try:
        date = parser.parse(
            combined_datetime,
            tzinfos=datetime.timedelta(0),
            dayfirst=True)
        date = date.replace(tzinfo=pytz.utc)
        return int(date.timestamp())
    except Exception as e:
        log.error(combined_datetime)
        log.error(str(e))
        log.error(format_exc())
        return 0


def get_voting_ids(flow_link):
    flow_parsed = False
    attempt = 0
    while attempt < NUMBER_OF_ATTEMPTS or not flow_parsed:
        attempt += 1
        try:
            flow_page = pq(url=flow_link, opener=pq_opener)
            dates_times = flow_page(VOTING_DATES_SELECTOR).text().split()
            dates = dates_times[0::2]
            times = dates_times[1::2]
            voting_ids = list(map(parse_date, dates, times))
            flow_parsed = True
            return voting_ids
        except Exception:
            log.error(flow_link)
            log.error(format_exc())
    return []


def get_bills_features(link):
        try:
            page = pq(url=link, opener=pq_opener_with_container_check)
        except Exception:
            return {}
        features = {}
        features['initiator'] = page(INITIATOR_SELECTOR).next().text()
        features['edition'] = page(EDITION_SELECTOR).next().text()
        features['sphere'] = page(SPHERE_SELECTOR).next().text()
        committee_dd_text = page(MAIN_COMMITTEE_SELECTOR).next('dd').text()
        features['main_committee'] = \
            committee_strip(committee_dd_text)
        if not features['main_committee']:
            features['main_committee'] = committee_dd_text
            log.critical(link)
            committee_html = page(MAIN_COMMITTEE_SELECTOR).outer_html()
            if committee_html:
                log.critical(committee_html)
            else:
                log.critical(page.outer_html())
        other_committees_raw = str(
            page(OTHERS_COMMITTEES_SELECTOR).next().children()
            ).replace('</li>', '').split('<li>')[1:]
        features['others_committees'] = list(map(
            committee_strip, other_committees_raw))
        features['last_status'] = page(LAST_STATUS_SELECTOR).text()
        stage_lines = list(map(get_updates, page(STAGE_SELECTOR)))
        features['stages'] = list(map(lambda x: x[0], stage_lines))
        features['dates_updated'] = list(map(lambda x: x[1], stage_lines))
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
            authors = authors[:-1]
            authors = list(map(lambda s: s.strip(), authors))
            features['authors']['name'] = authors
            features['authors']['id'] = list(map(lambda s: ids[s], authors))
        else:
            authors = un_standard_names(authors)
            features['authors']['name'] = authors
            features['authors']['id'] = list(map(lambda s: ids[s], authors))
        try:
            flow_link = FLOW_LINK_TEMPLATE + \
                page(FLOW_LINK_SELECTOR).attr('href')
        except Exception:  # TypeError
            log.warning(format_exc())
            log.warning(page.outer_html())
            flow_link = None
        if flow_link:
            features['voting_ids'] = get_voting_ids(flow_link)
        else:
            features['voting_ids'] = []
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

if __name__ == "__main__":
    # setting sockets to run script anonymously
    socks.setdefaultproxy(
        proxy_type=socks.PROXY_TYPE_SOCKS5,
        addr="127.0.0.1", port=9050)
    socket.socket = socks.socksocket

    # open json with MP ids
    with open(PERSON_IDS_FILE) as json_data:
            ids = json.load(json_data)
            json_data.close()

    # this loop executes till all bills are downloaded
    scrapper_failed = True
    while scrapper_failed:
        scrapper_failed = False
        unique_docs = []
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
        log.debug("Downloading bills...")
        bills_downloaded = False
        attempt = 1
        while not bills_downloaded and attempt <= NUMBER_OF_ATTEMPTS:
            try:
                bill_list = rada.list_bills()
                bills_downloaded = True
            except Exception:
                log.warning("Cannot download bills list. Retrying later.")
                bills_downloaded = False
                attempt += 1
                time.sleep(LONG_SLEEP * 5)
        if not bills_downloaded:
            break
        keys = list(bill_list.keys())
        for i in range(len(keys)):
            log.info(str(i + 1) + " of " + str(len(keys)))
            key = keys[i]
            if key in bills_dict.keys():
                now = int(datetime.datetime.now().strftime("%s"))
                if (now - bills_dict[key]['update_time']) > UPDATE_LIMIT:
                    bills_dict[key] = download_bill(key)
            else:
                bills_dict[key] = download_bill(key)
            if scrapper_failed:
                log.warning("Something went wrong, pausing before a retry")
                time.sleep(LONG_SLEEP)
                break
            if getattr(bills_dict[key], 'bill_docs', {}):
                unique_docs = list(set(unique_docs +
                                       bills_dict[key]['bill_docs']['name']))
            if getattr(bills_dict[key], 'flow_docs', {}):
                unique_docs = list(set(unique_docs +
                                       bills_dict[key]['flow_docs']['name']))
            write_general_info(key)
            append_committee(key)
        general_info_csv.close()

    if bills_downloaded:
        write_committees_list()
        write_docs_list()
