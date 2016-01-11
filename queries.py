#!/usr/bin/env python3
from pyquery import PyQuery as pq
from csv import writer
import re
from time import sleep

from rada import rada

OUTPUT_FOLDER = '../output/'
OUTPUT_FILE = OUTPUT_FOLDER + 'queries.csv'
SLEEP_TIME = 0.5
LINK_TEMPLATE = "http://w1.c1.rada.gov.ua/pls/zweb2/wcadr43D?sklikannja" \
                "={parliament:d}&kodtip={type_id:d}&rejim=1&KOD8011=" \
                "{deputy_id:d}"
QUERY_LINK_TEMPLATE = 'http://w1.c1.rada.gov.ua/pls/zweb2/'
NAME_SELECTOR = '.heading h3 b'
DEPUTY_ID_RE = re.compile(
                    "http://itd.rada.gov.ua/mps/info/page/(?P<deputy_id>\d+)")


ROW_HEADERS = (
    'name',
    'category',
    'number',
    'date',
    'session',
    'link',
    'whom',
    'title',
    'status',
)

template_arguments = {
    'parliament': rada.PARLIAMENT_NUMBER,
    'deputy_id': None,
    'type_id': None
}

QUERY_TYPES = {
  1: 'Президенту України',
  4: 'Голові Верховної Ради України, керівникам' \
        'комітетів Верховної Ради України',
  5: 'Кабінету Міністрів України',
  6: 'Керівникам міністерств і відомств України',
  7: 'Генеральному прокурору України',
  8: 'Місцевим органам влади і управління'
}

ROW_SELECTOR = 'table:eq(1) tr'
ROW_SUBSELECTORS = (
    'td.THEAD3:nth-child(1) a',
    'td.THEAD21:nth-child(2)',
    'td.THEAD3:nth-child(3)',
    'td.THEAD21:nth-child(4)',
)



print("getting deputies list")
mps = rada.list_deputy_links()
names = list(map(lambda x: pq(x).text(), mps))

fh = open(OUTPUT_FILE, 'w')
csvwriter = writer(fh)
csvwriter.writerow(ROW_HEADERS)
mp_number = 0
for link in [link.attrib['href'] for link in mps]:
    deputy_id_matched = DEPUTY_ID_RE.fullmatch(link)
    if deputy_id_matched:
        template_arguments['deputy_id'] = int(
            deputy_id_matched.group('deputy_id'))
        for type_id in QUERY_TYPES.keys():
            sleep(SLEEP_TIME)
            template_arguments['type_id'] = type_id
            queries_link = LINK_TEMPLATE.format(**template_arguments)
            queries_page = pq(queries_link)
            query_type = QUERY_TYPES[type_id]
            print(names[mp_number], '-', query_type)
            for row in queries_page(ROW_SELECTOR):
                row_pq = pq(row)
                first_column = row_pq(ROW_SUBSELECTORS[0])
                if first_column.text() != '':
                    query_link = QUERY_LINK_TEMPLATE + str(
                        first_column.attr('href'))
                    query_num = first_column.text().split()[0]
                    query_date = first_column.text().split()[1].split('(')[0]
                    query_session = first_column.text().split(' ')[2] \
                        + " " + first_column.text().split(' ')[3]
                    row_output = [names[mp_number], query_type, query_num,
                                  query_date, query_session, query_link, ]
                    for subselector in ROW_SUBSELECTORS[1:4]:
                        row_output.append(row_pq(subselector).text())
                    if row_output[6]:
                        csvwriter.writerow(row_output)
    mp_number += 1
fh.close()
