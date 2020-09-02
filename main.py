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

import argparse


parser = argparse.ArgumentParser()

parser.add_argument('-B', "--borough", type= str)
parser.add_argument('-S', '--start_date', help='delimited list input', type=str)
parser.add_argument('-E', '--end_date',  type=str)
parser.add_argument('-M', '--mode', type=str)
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
        from Haringey import Haringey
        s = Haringey()
        s.scape_search_results(start, end)
    elif args.borough == "Harrow":
        from Harrow import Harrow
        s = Harrow()
    else:
        if args.borough == "Midlothian":
            from Midlothian import Midlothian
            s = Midlothian()

        else:
            from Scraper import Scraper
            s = Scraper(borough)

    
        
        if args.start_date == None and args.end_date == None:
            s.get_cases_from_all_weeks():

        else:
            s.scrape_search_within_dates(args.start_date, args.end_date)
        s.csv_to_excel()