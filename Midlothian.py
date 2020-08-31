import requests
from bs4 import BeautifulSoup as bs
import csv
from scraper import Scraper
import json


midlothian = Scraper("Midlothian")
midlothian.scrape_everything()


class Midlothian(Scraper):

    #GETS CSRF & WEEK DATA

        
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
            self.cases[week]["total_cases"] = total_cases_for_week
        except:
            total_cases_for_week = len(searchResultsContainer_soup.find_all("li"))
            self.cases[week]["total_cases"] = total_cases_for_week
       


    def scrape_cases_urls(self, week):
        page_number = 1
        self.weeks_results[week] = []
        total = self.cases[week]["total_cases"]
        for page in range(0, total, 100):
            search_criteria_data = {'_csrf' : self.csrf, "searchCriteria.page": page_number,"action": "page","orderBy": "DateReceived","orderByDirection": "Descending", "searchCriteria.resultsPerPage": "100"}
            next_page = self.s.post(self.url_paged_results, data = search_criteria_data)
            next_page_soup = bs(next_page.text, "lxml")
            next_page_results_soup = next_page_soup.find_all(id = "searchresults")[0].find_all("li")
            self.weeks_results[week].extend(next_page_results_soup)
            page_number += 1

