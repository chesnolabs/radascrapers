import re
from csv import writer
from pyquery import PyQuery as pq

START_PAGE = "http://w1.c1.rada.gov.ua/pls/site2/p_fractions"
TEMPLATE_PAGE = "http://w1.c1.rada.gov.ua/pls/site2/"


COMMITTEE_SELECTOR = "td:nth-child(1) a"
MEMBER_SELECTOR = ".topTitle a"

FACT_TEMPLATE = "http://w1.c1.rada.gov.ua/pls/site2/p_fraction_list?pidid={fact_id:s}"

FACTID_RE = re.compile("/page/(?P<fact_id>\d+)")

OUTPUT_FILE = "../output/mps_facts.csv"

HEADERS = ["MP", "faction"]

start_page = pq(START_PAGE)

facts = start_page(COMMITTEE_SELECTOR)

output = []
for f in facts:
    f = pq(f)
    faction = f.text()
    if "не входять" not in faction and "Схема" not in faction:
        href = f.attr("href")
        print(faction, href)
        fact_id = FACTID_RE.search(href).group("fact_id")
        fact_page = pq(FACT_TEMPLATE.format(fact_id = fact_id))
        members = fact_page(".topTitle a")
        for m in members:
            m = pq(m)
            name = m.text()
            output.append([name, faction])
    elif "не входять" in faction:
        href = f.attr("href")
        print(faction, href)
        faction_href = TEMPLATE_PAGE + href
        print(faction_href)
        fact_page = pq(faction_href)
        members = fact_page("div.information_block li a")
        for m in members:
            m = pq(m)
            name = m.text()
            output.append([name, faction])
        

with open(OUTPUT_FILE, "w") as of:
    csvwriter = writer(of)
    csvwriter.writerow(HEADERS)
    for r in output:
        csvwriter.writerow(r)
        
