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

    #contacts = [pq(i).attr('href') for i in page(INFORMATION_BLOCK_SELECTOR) if (not 'rada.gov.ua' in pq(i).attr('href')) and "http" in pq(i).attr('href')]
    #return contacts
    #print(contacts)
    #print(len(page(CONTACTS_SELECTOR)))

def get_emails(page):
    emails = [pq(i).attr('href').replace('mailto:','') for i in page(INFORMATION_BLOCK_SELECTOR) if "@" in pq(i).attr('href')]
    return emails
    
def get_platform(s):
    print(s)
    return PLATFORM_RE.search(s).group(0).replace('www.','')

def get_social_medias(list_):
    medias = []
    for l in list_:
        for social_media in  SOCIAL_MEDIAS:
            for media_part in social_media:
                if media_part in l:
                    medias.append(l)
    return medias


fh = open(OUTPUT_FILE,'w')
csvwriter = writer(fh)
csvwriter.writerow(HEADERS)

platforms = {}
pre_link_list = rada.list_deputy_links()
link_list = [pq(l).attr('href') for l in pre_link_list]

for link in link_list:
    page = pq(link)
    name = page(NAME_SELECTOR)
    name = pq(name).text()
    info = get_basic_info(page)
    #contacts = get_contact_data(page)
    #for c in contacts:
    #    print(name, get_platform(c))
    #emails = get_emails(page)
    #social_media = get_social_medias(contacts)
    #websites = list(set(contacts) - set(social_media))
    #print(social_media)
    #for sm in social_media:
    #    output_row = [name, sm, 'social_media']
    #    csvwriter.writerow(output_row)
    #for wb in websites:
    #    output_row = [name, wb, 'website']
    #    csvwriter.writerow(output_row)
    #for e in emails:
    output_row = [name] + info
    csvwriter.writerow(output_row)
    sleep(SLEEP_TIME)

fh.close()
