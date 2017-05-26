from pyquery import PyQuery as pq
from rada import rada
from time import sleep
from csv import writer
import re

OUTPUT_FILE = "../output/lists_districts.csv"
SLEEP_TIME = 0.5

BASIC_INFO_SELECTOR = "div.mp-general-info"
NAME_SELECTOR = "h2"

NUMBER_SELECTOR = re.compile("(?P<number>\d+)\s+Дата")
DISTRICT_SELECTOR = re.compile("округу №(?P<district_number>\d+)\s+Регіон")
REGION_SELECTOR = re.compile("Регіон:\s+(?P<region>.*)\s+Дата")
PARTY_SELECTOR = re.compile("Партія:\s+(?P<party>.*)\s+Номер")

HEADERS = ["MP", 'party', 'list_number', "region", "district"]

def get_basic_info(page):
	b_info = page(BASIC_INFO_SELECTOR).text()
	number_matched = NUMBER_SELECTOR.search(b_info)
	number, district, party, region = "", "", "", ""
	if number_matched:
		number = number_matched.group('number')
		print(number)
	ditrict_matched = DISTRICT_SELECTOR.search(b_info)
	if ditrict_matched:
		district = ditrict_matched.group('district_number')
		print(district)
	region_matched = REGION_SELECTOR.search(b_info)
	if region_matched:
		region = region_matched.group('region')
		print(region)
	party_matched = PARTY_SELECTOR.search(b_info)
	if party_matched:
		party = party_matched.group('party')
		print(party)
	return([party, number, region, district])

fh = open(OUTPUT_FILE,'w')
csvwriter = writer(fh)
csvwriter.writerow(HEADERS)

pre_link_list = rada.list_deputy_links()
link_list = [pq(l).attr('href') for l in pre_link_list]

for link in link_list:
    page = pq(link)
    name = page(NAME_SELECTOR)
    name = pq(name).text()
    info = get_basic_info(page)
    output_row = [name] + info
    csvwriter.writerow(output_row)
    sleep(SLEEP_TIME)

fh.close()
