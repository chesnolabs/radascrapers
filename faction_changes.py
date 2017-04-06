from pyquery import PyQuery as pq
from csv import writer
from time import sleep
import re

from rada import rada
from settings import OUTPUT_FOLDER, PERSON_IDS_FILE

PARLIAMENT_NUMBER = 9
LIST_URL = 'http://w1.c1.rada.gov.ua/pls/site2/fetch_mps?skl_id={parliament:d}'
LIST_URL = LIST_URL.format(**{'parliament': PARLIAMENT_NUMBER})
#CHANGE_PARTICLE = '&SKL={parliament:d}'.format(
#                            **{'parliament': PARLIAMENT_NUMBER})
CHANGE_PARTICLE = ''
#PAGE_PARTICLE = '/{parliament:d}'.format(
#                            **{'parliament': PARLIAMENT_NUMBER})
PAGE_PARTICLE = ''
#EX_PAGE_PARTICLE = 'ex'
EX_PAGE_PARTICLE = ''

ROW_SELECTOR = 'div.information_block table tr:gt(0)'
COLUMN_SELECTOR = 'td'
OUTPUT_FILE = OUTPUT_FOLDER + 'faction_changes_{p_number:d}.csv'.format(
                                        **{'p_number': PARLIAMENT_NUMBER - 1}
                                                        )

HEADERS = ["name", "faction", "start_date", "end_date"]
SLEEP_TIME = 0.3

#MP_PAGE_RE = re.compile('http://itd.rada.gov.ua/mps/info/{ex_page:s}page/(?P<ID>\d+)'.format(
#                                **{'ex_page': EX_PAGE_PARTICLE}) + PAGE_PARTICLE)
MP_PAGE_RE = re.compile('http://itd.rada.gov.ua/mps/info/{ex_page:s}page/(?P<ID>\d+)'.format(
                                **{'ex_page': EX_PAGE_PARTICLE}) + PAGE_PARTICLE)
FACTION_CHANGES_URL = 'http://w1.c1.rada.gov.ua/pls/site2/p_{ex_page:s}deputat_fr_changes?d_id={mp_id:d}' + CHANGE_PARTICLE

print('http://itd.rada.gov.ua/mps/info/page/(?P<deputy_id>\d+)' + PAGE_PARTICLE)
print(MP_PAGE_RE)

def change_date_format(s):
    parts = s.split(".")
    return parts[2] + '-' + parts[1] + '-' + parts[0]


def parse_changes_table(url):
    print(name)
    print(url)
    page = pq(url)
    rows = page(ROW_SELECTOR)
    for r in rows:
        r = pq(r)
        print(r.text())
        cols = r(COLUMN_SELECTOR)
        cells = list(map(lambda x: pq(x).text(), cols))
        start_date = change_date_format(cells[1])
        if cells[2] != "-":
            end_date = change_date_format(cells[2])
        else:
            end_date = ""
        faction_title = cells[0]
        output_row = [name, faction_title, start_date, end_date]
        output_csv_writer.writerow(output_row)


output_csv = open(OUTPUT_FILE, 'w')
output_csv_writer = writer(output_csv)
output_csv_writer.writerow(HEADERS)


mps = rada.list_deputy_links()
for mp in mps:
    name = pq(mp).text()
    page_link = pq(mp).attr('href')
    print(page_link)
    print(MP_PAGE_RE)
    page_link_matched = MP_PAGE_RE.fullmatch(page_link)
    print(page_link_matched)
    mp_id = int(page_link_matched.group('ID'))
    faction_changes_link = FACTION_CHANGES_URL.format(**{'ex_page': EX_PAGE_PARTICLE, 'mp_id': mp_id})
    parse_changes_table(faction_changes_link)
    sleep(SLEEP_TIME)
