import requests
from bs4 import BeautifulSoup as bs
import csv
import json
from datetime import datetime, date, time
import numpy as np
import pandas as pd
from os import path
import os.path
from scraper2 import Scraper


class HaringeyScraper(Scraper):

    def __init__(self):
        self.borough_name = "Haringey"
        self.url = "http://www.planningservices.haringey.gov.uk/portal/servlets/WeeklyListServlet"
        self.search_url = "http://www.planningservices.haringey.gov.uk/portal/servlets/ApplicationSearchServlet"
        self.first_part_url = "http://www.planningservices.haringey.gov.uk/portal/"
        self.cases = []
        self.search_data = {"ValidDateFrom":"11-05-2020","ValidDateTo":"15-05-2020"}
        self.next_page = {"LAST_ROW_ID":20,"DIRECTION":"F","RECORDS":20,"forward":"Next+Matching+Results"}  
        self.s = requests.Session()
        self.csv_file = self.borough_name + ".csv"
        if os.path.exists(self.csv_file) == False:
            self.write_header()
        
        self.get_done_case_numbers()
        

    #redundant
    def get_javascript_links(self):

        js_links = []
        request = requests.get(self.url)
        html_soup = bs(request.text, "lxml")
        trs = html_soup.table.find_all("tr")

        for tr in trs[1:]:
            week = {}
            tds = tr.find_all("td")
            js_link = tds[2].u.a["href"]
            week_starts = tds[0].center.text
            week_ends = tds[1].center.text
            js_links.append(js_link)
            week["start"] = week_starts
            week["end"] = week_ends
            week["js_link"] = js_link
            week["app_quantity"] = int(tds[2].u.a.text)
            self.weeks.append(week)
        return js_links
    

    def scrape_from_search_soup(self):
        for tr in self.cases_to_scrape:
            tds = tr.find_all("td")
            case = {}
            case["case_number"] = tds[0].text 
            link = self.first_part_url + tds[0].a["href"][3:]
            case["site_address"] = tds[1].text 
            case["proposal"] = tds[5].text
            case["status"] = tds[6].text
            case_page = requests.get(link)
            case_page_soup = bs(case_page.text, "lxml")
            case_trs = case_page_soup.table.find_all("tr")
            case["app_received_date"] = case_trs[4].find_all("td")[1].input["value"]
            case["consulation_end_date"] = case_trs[4].find_all("td")[3].input["value"]
            case["application_decision_date"] = case_trs[5].find_all("td")[3].input["value"]
            case["applicant_name"] = case_trs[8].find_all("td")[1].input["value"]
            case["agent_name"] = case_trs[8].find_all("td")[3].input["value"]
            case["applicant_address"] = case_trs[9].find_all("td")[1].text
            case["agent_address"] = case_trs[9].find_all("td")[3].text
            self.cases[case["case_number"]] = case
                

    
    def scape_search_results(self, start, end):
        # date format 15-05-2020
        self.s.get(self.search_url)
        s = requests.Session()
        cases_first_20 = s.post(self.search_url, {"ValidDateFrom": start,"ValidDateTo": end})
        cases_20_soup = bs(cases_first_20.text, "lxml")
        trs = cases_20_soup.table.find_all("tr")
        self.cases_to_scrape = trs[1:len(trs)-1]
        form2 = cases_20_soup.table.find("form",{"name": "navigationForm2"})
        last_row_id = 20
        while form2 != None:
                # DO UNTIL NAVIGATION FORM 2 IS GONE
                data = {'LAST_ROW_ID': last_row_id, 'DIRECTION': 'F', 'RECORDS': 20, 'forward': 'Next+Matching+Results'}  
                next_page = s.post(self.search_url, data)
                next_page_soup = bs(next_page.text, "lxml")
                trs = next_page_soup.table.find_all("tr")
                cases_to_add = trs[1:len(trs)-1]
                self.cases_to_scrape.extend(cases_to_add)

                form2 = next_page_soup.table.find("form",{"name": "navigationForm2"})
                last_row_id += 20
                #WHILE LOOP FOR FORM2?
            
        



