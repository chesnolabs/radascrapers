from pyquery import PyQuery as pq
from lib import rada
from time import sleep
from csv import writer
import re

OUTPUT_FILE = "output/contacts.csv"
SLEEP_TIME = 0.5

SOCIAL_MEDIAS = [['facebook'], ['vk.com','vkontakte'], ['livejournal'], ['instagram'], ['twitter'],]

PLATFORM_RE = re.compile("(www\.)?\w+\.[\w\.]+")

INFORMATION_BLOCK_SELECTOR = "div.information_block_ins:last div a"
NAME_SELECTOR = "h2"


HEADERS = ["MP", 'adress', 'type']

def get_contact_data(page):
    contacts = [pq(i).attr('href') for i in page(INFORMATION_BLOCK_SELECTOR) if (not 'rada.gov.ua' in pq(i).attr('href')) and "http" in pq(i).attr('href')]
    return contacts
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
    contacts = get_contact_data(page)
    for c in contacts:
        print(name, get_platform(c))
    emails = get_emails(page)
    social_media = get_social_medias(contacts)
    websites = list(set(contacts) - set(social_media))
    #print(social_media)
    for sm in social_media:
        output_row = [name, sm, 'social_media']
        csvwriter.writerow(output_row)
    for wb in websites:
        output_row = [name, wb, 'website']
        csvwriter.writerow(output_row)
    for e in emails:
        output_row = [name, e, 'e-mail']
        csvwriter.writerow(output_row)
    
    sleep(SLEEP_TIME)

fh.close()
