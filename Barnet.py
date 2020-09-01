import requests
from bs4 import BeautifulSoup as bs
import csv
from Scraper2 import Scraper
import json
import argparse

parser = argparse.ArgumentParser()

parser.add_argument('-S', '--Start_Data', help='delimited list input', type=str)
parser.add_argument('-E', '--End_Data',  type=str)
args = parser.parse_args()
a = "b"

print(args)

print(args.End_Data)

if a == "all":
    barnet = Scraper("Barnet")
    barnet.get_cases_from_all_weeks()
    barnet.scrape_all_cases_to_csv()
    barnet.csv_to_excel()
