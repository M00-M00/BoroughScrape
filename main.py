import requests
from bs4 import BeautifulSoup as bs
import csv
import json
from datetime import datetime, date, time
import numpy as np
import pandas as pd
from os import path
import os.path
from xlsxwriter.workbook import Workbook
import glob
from Scraper2 import Scraper
from Midlothian import Midlothian
from Haringey import Haringey
from Harrow import Harrow
import argparse


parser = argparse.ArgumentParser()

parser.add_argument('-B', "--borough", type= str)
parser.add_argument('-S', '--start_date', help='delimited list input', type=str)
parser.add_argument('-E', '--end_date',  type=str)
args = parser.parse_args()

borough = "Edinburgh"
start = args.start_date
end = args.end_date



if __name__ == "__main__":

        
    if args.borough == None:
        print("No borough selected, please typ what borough to parse")
        borough = str(input())

    if args.start_date == None:
        print("h")

    if borough == "None":
        print("test")
    elif args.borough == "Haringey":
        s = Haringey()
        s.scape_search_results(start, end)
    elif args.borough == "Harrow":
        s = Harrow()
    else:
        if args.borough == "Midlothian":
            s = Midlothian()
        else:
            s = Scraper(borough)

        s.get_cases_from_all_weeks()
        
        if args.start_date == None and args.end_date == None:
            s.scrape_all_cases_to_csv()
        else:
            s.scrape_cases_within_dates(args.start_date, args.end_date)
        s.csv_to_excel()