#!/usr/bin/env python3
# coding:utf-8
from pyquery import PyQuery as pq
from csv import writer
import re
from time import sleep

from lib import rada

OUTPUT_FILE = 'output/legislative_activity.csv'
NAME_STRIP = " (народний депутат VIII скл.)"
SLEEP_TIME = 0.5
LINK_TEMPLATE = "http://w1.c1.rada.gov.ua/pls/pt2/reports.dep2?"\
    "PERSON={deputy_id:d}&SKL={parliament:d}"
DEPUTY_ID_RE = re.compile(
    "http://itd.rada.gov.ua/mps/info/page/(?P<deputy_id>\d+)")

NAME_SELECTOR = '.heading h3'
ROW_SELECTOR = '.information_block_ins table:first tr'
ROW_SUBSELECTORS = (
    'td:nth-child(1) a',
    'td:nth-child(2) i',
    'td:nth-child(3)',
    'td:nth-child(4)',
)
ROW_HEADERS = (
    'name',
    'bill_number',
    'date',
    'bill_title',
    'law',
    'type',
)

template_arguments = {
    'parliament': rada.PARLIAMENT_NUMBER,
    'deputy_id': None
}

ACT_TYPES = {
    "Проект Закону": 'закон',
    "Проект Постанови": 'постанова',
}
ACT_TYPE_OTHER = "інше"

print('getting acts list')
acts = rada.list_acts()
for act_number in acts:
    for act_type in ACT_TYPES:
        print(act_number)
        if acts[act_number][1].startswith(act_type):
            acts[act_number].append(ACT_TYPES[act_type])
    if len(acts[act_number]) == 2:
        acts[act_number].append(ACT_TYPE_OTHER)

print('getting deputies list')
list = rada.list_deputy_links()

fh = open(OUTPUT_FILE, 'w')
csvwriter = writer(fh)
csvwriter.writerow(ROW_HEADERS)

for link in [link.attrib['href'] for link in list]:
    sleep(SLEEP_TIME)
    deputy_id_matched = DEPUTY_ID_RE.fullmatch(link)
    if deputy_id_matched:
        template_arguments['deputy_id'] = \
            int(deputy_id_matched.group('deputy_id'))
        legislative_link = LINK_TEMPLATE.format(**template_arguments)
        legislative_page = pq(legislative_link)
        deputy_name = legislative_page(NAME_SELECTOR).text()\
            .replace(NAME_STRIP, '')
        print(deputy_name)
        for row in legislative_page(ROW_SELECTOR):
            row_pq = pq(row)
            row_output = [deputy_name, ]
            for subselector in ROW_SUBSELECTORS:
                row_output.append(row_pq(subselector).text())
            if row_output[1]:
                row_output.append(acts[row_output[1]][2])
                csvwriter.writerow(row_output)
    else:
        print('Update DEPUTY_ID_RE.')
        raise Exception
        # TODO: визначити на сторінці депутата
        # deputy_page = pq(link)

fh.close()
