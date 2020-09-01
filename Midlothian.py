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




class Midlothian(Scraper):

    def __init__(self):

        self.borough_name = "Midlothian"
        self.cases = {}

        self.weeks = {}

        with open ("borough.json", "r") as j:

            data = json.load(j)
        
            self.url_base = data[self.borough_name]["url_base"]

            self.url_for_case_base = data[self.borough_name]["url_for_case_base"]

        self.url_start = self.url_base + "/search.do?action=weeklyList"

        self.url_search_start =  self.url_base + "/weeklyListResults.do?action=firstPage"

        self.url_paged_results = self.url_base + "/pagedSearchResults.do"

        self.s = requests.Session()

        self.csv_columns = ["reference", "alternative reference", "address", "proposal", "status", "applicant name", "agent name", "agent address", "agent phone number", "agent email", "application received", "application validated", "decision issued date", "decision"]

        self.weeks_selection = []
    
        self.get_csrf_token()

        self.get_week_selection()

        self.quantity_of_cases = {}

        self.weeks_results = {}

        self.csv_file = self.borough_name + ".csv"

        self.done_case = []

        self.failed_cases = []

        self.load_cases_data_from_json()

        if os.path.exists(self.csv_file) == False:
            self.write_header()
        
        self.get_done_case_numbers()


    def get_csrf_token(self):
       
        start_search = self.s.get(self.url_start)
        s_search_soup = bs(start_search.text, "lxml")  
        self.csrf = s_search_soup.find(id="weeklyListForm").input["value"]


    def search_for_week_start(self, week):
        search_start_data = {'_csrf' : self.csrf, 'searchCriteria.parish': '', 'searchCriteria.ward': '', 'week': week, 'dateType': 'DC_Validated', 'searchType': 'Application'}

        search_start = self.s.post(self.url_search_start, data = search_start_data)
        search_soup = bs(search_start.text, "lxml")
        searchResultsContainer_soup = search_soup.find_all(id = "searchResultsContainer")[0]
        ###get total cases for the week
        try:
            total_cases_for_week = int(searchResultsContainer_soup.span.text.split(" of ")[1])
            self.weeks[week]["total_cases"] = total_cases_for_week
        except:
            total_cases_for_week = len(searchResultsContainer_soup.find_all("li"))
            self.weeks[week]["total_cases"] = total_cases_for_week
       


    def scrape_weekly_search_results(self, week):
        page_number = 1
        self.weeks_results[week] = []
        total = self.weeks[week]["total_cases"]
        for page in range(0, total, 100):
            search_criteria_data = {'_csrf' : self.csrf, "searchCriteria.page": page_number,"action": "page","orderBy": "DateReceived","orderByDirection": "Descending", "searchCriteria.resultsPerPage": "100"}
            next_page = self.s.post(self.url_paged_results, data = search_criteria_data)
            next_page_soup = bs(next_page.text, "lxml")
            next_page_results_soup = next_page_soup.find_all(id = "searchresults")[0].find_all("li")
            self.weeks_results[week].extend(next_page_results_soup)
            page_number += 1

