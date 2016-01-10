#!/usr/bin/env python3
# coding:utf-8
from pyquery import PyQuery as pq
from httplib2 import Http

PARLIAMENT_NUMBER = 9
LIST_URL = 'http://w1.c1.rada.gov.ua/pls/site2/fetch_mps?skl_id={parliament:d}'
LIST_URL = LIST_URL.format(**{'parliament': PARLIAMENT_NUMBER})
LIST_ELEMENT = 'ul.search-filter-results-thumbnails li'
# ELEMENT_IMG = 'p.thumbnail img'
ELEMENT_LINK_TAG = 'p.title a'

ACTS_PARLIAMENT_NUMBER = 10000 + PARLIAMENT_NUMBER
ACTS_LIST_URL = 'http://w1.c1.rada.gov.ua/pls/zweb2/webproc2_5_1_J?'\
    'ses={parliament:d}&zp_cnt=-1'
ACTS_LIST_URL = ACTS_LIST_URL.format(**{'parliament': ACTS_PARLIAMENT_NUMBER})

ACT_SELECTOR = '.information_block_ins table tr'
ACT_SUBSELECTORS = (
    'td:nth-child(1) a',
    'td:nth-child(2)',
    'td:nth-child(3)',
)

USERAGENT = "Mozilla/5.0 (X11; Linux i686) (KHTML, Gecko) Chrome/40.0.1234.56"

http = Http('.cache', timeout=10)


def list_deputy_links():
    q = pq(url=LIST_URL)
    return q(' '.join((LIST_ELEMENT, ELEMENT_LINK_TAG)))


def list_acts(return_list=False):
    q = pq(url=ACTS_LIST_URL)
    acts_list = list()
    for act in q(ACT_SELECTOR):
        act_pq = pq(act)
        row = list()
        for subselector in ACT_SUBSELECTORS:
                row.append(act_pq(subselector).text())
        if row[0]:
            acts_list.append(row)
    if return_list:
        return acts_list
    acts_dict = dict()
    for act in acts_list:
        acts_dict[act[0]] = act[1:3]
    return acts_dict


def download(url, filename):
    try:
        response, content = \
            http.request(url, headers={'User-Agent': USERAGENT})

        with open(filename, 'wb') as filehandler:
            filehandler.write(content)
    except Exception as e:
        print(str(e))
