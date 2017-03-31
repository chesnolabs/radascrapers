from pyquery import PyQuery as pq
from lib import rada
from time import sleep
from csv import writer

ROW_HEADERS = [
  "MP_name", "birth_date", "start_date", "end_date" 
  ]

OUTPUT_FILE = "output/birth_dates.csv"

BIRTH_DATE_SELECTOR_1 = "table.simple_info:eq(1)"
BIRTH_DATE_SELECTOR_2 = "tr:eq(0)"
BIRTH_DATE_SELECTOR_3 = "td:eq(1)"
COMMITTEE_SELECTOR = "ul.level1 li:eq(0)"
DATES_SELECTOR = "table.simple_info"
NAME_SELECTOR = "h2"

SLEEP_TIME = 0.5

MONTHES_LIT = [" січня ", " лютого "," березня ", " квітня ", " травня ", " червня ", " липня ", " серпня ", " вересня ", " жовтня ", " листопада ", " грудня "]
MONTHES_DIG = [".01.", ".02.",".03.", ".04.", ".05.", ".06.", ".07.", ".08.", ".09.", ".10.", ".11.", ".12."]
RADA_ID_RE = re.compile("http://itd.rada.gov.ua/mps/info/page/(?P<rada_id>[0-9]{1,6})")

def monthes_change(s):
  for i in range(len(MONTHES_LIT)):
    s = s.replace(MONTHES_LIT[i], MONTHES_DIG[i])
  s = s.replace(" ","")
  s = s.replace("р.","")
  return s

fh = open(OUTPUT_FILE,'w')
csvwriter = writer(fh)
csvwriter.writerow(ROW_HEADERS)

link_list = rada.list_deputy_links()

for link in link_list:
  link = pq(link).attr("href")
  page = pq(link)
  name = page(NAME_SELECTOR)
  name = pq(name).text()
  birth_date = page(BIRTH_DATE_SELECTOR_1)
  birth_date = birth_date(BIRTH_DATE_SELECTOR_2)
  birth_date = birth_date(BIRTH_DATE_SELECTOR_3)
  birth_date = monthes_change(pq(birth_date).text())
  #committee = page(COMMITTEE_SELECTOR).text()
  dates = page(DATES_SELECTOR).text().split(":")
  start_date = monthes_change(dates[1].split("р.")[0])
  end_date = monthes_change(dates[2].split("р.")[0])
  print(name, birth_date, start_date, end_date)
  output_row = [name, birth_date, start_date, end_date]
  csvwriter.writerow(output_row)

  sleep(SLEEP_TIME)

fh.close()
