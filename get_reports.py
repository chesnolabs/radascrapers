from lib import rada
import translitua
from pyquery import PyQuery as pq
import urllib.request
import re
from time import sleep
import os

REPORT_PAGE_TEMPLATE = "http://itd.rada.gov.ua/declview/home/report/{mp_id_rep:s}"
MP_LINK_RE = re.compile("http://itd.rada.gov.ua/mps/info/page/(?P<mp_id>\d+)")
REPORT_SELECTOR = "table a"
MP_NAME_SELECTOR = "div.information_block_ins h3"

LINK_FIRST_PART = "http://itd.rada.gov.ua"

SLEEP_TIME = 2.5

pre_link_list = rada.list_deputy_links()
link_list = [pq(l).attr('href') for l in pre_link_list]
#urllib.URLopener.version = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1'



for link in link_list:
    link_matched = MP_LINK_RE.fullmatch(link)
    mp_id = link_matched.group("mp_id")
    link_report = REPORT_PAGE_TEMPLATE.format(mp_id_rep = mp_id)
    page = pq(link_report)
    reports = page(REPORT_SELECTOR)
    name = page(MP_NAME_SELECTOR).text().replace(" - Звіти народного депутата", "")
    print(name)
    for r in reports:
        if not os.path.exists(os.path.join('reports',name)):
            os.makedirs(os.path.join('reports',name))
        full_link = LINK_FIRST_PART + pq(r).attr("href")
        #req = urllib.request.Request(full_link)
        #req.add_header('User-Agent', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1')
        if not os.path.exists(os.path.join("reports", name, r.text)):
            urllib.request.urlretrieve(full_link, os.path.join("reports", name, r.text))
        sleep(SLEEP_TIME)
    sleep(SLEEP_TIME)