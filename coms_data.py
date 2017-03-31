import re
from csv import writer
from pyquery import PyQuery as pq

START_PAGE = "http://w1.c1.rada.gov.ua/pls/site2/p_komitis"
COMMITTEE_SELECTOR = "td:nth-child(1) a"
MEMBER_SELECTOR = ".topTitle a"

COM_TEMPLATE = "http://w1.c1.rada.gov.ua/pls/site2/p_komity_list?pidid={com_id:s}"

COMID_RE = re.compile("p_komity\?pidid=(?P<com_id>\d+)")

OUTPUT_FILE = "../output/mps_coms.csv"

HEADERS = ["MP", "committee"]

start_page = pq(START_PAGE)

coms = start_page(COMMITTEE_SELECTOR)

output = []
for c in coms:
    c = pq(c)
    committee = c.text()
    if "не входять" not in committee:
        href = c.attr("href")
        print(committee, href)
        com_id = COMID_RE.fullmatch(href).group("com_id")
        com_page = pq(COM_TEMPLATE.format(com_id = com_id))
        members = com_page(".topTitle a")
        for m in members:
            m = pq(m)
            name = m.text()
            output.append([name, committee])

with open(OUTPUT_FILE, "w") as of:
    csvwriter = writer(of)
    csvwriter.writerow(HEADERS)
    for r in output:
        csvwriter.writerow(r)
        
