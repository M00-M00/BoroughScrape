import requests
from bs4 import BeautifulSoup as bs
import csv
import json
from datetime import datetime, date, time
import numpy as np
import pandas as pd
from os import path
import os.path

class Scraper():
    
    def __init__(self, borough_name):

        self.borough_name = borough_name

        with open ("borough.json", "r") as j:

            data = json.load(j)
        
            self.url_base = data[self.borough_name]["url_base"]

            self.url_for_case_base = data[self.borough_name]["url_for_case_base"]

        self.url_start = self.url_base + "/search.do?action=weeklyList"

        self.url_search_start =  self.url_base + "/weeklyListResults.do?action=firstPage"

        self.url_paged_results = self.url_base + "/pagedSearchResults.do"

        self.s = requests.Session()

        self.csv_columns = ["reference", "alternative reference", "address", "proposal", "status", "applicant name", "agent name", "agent address", "agent phone number", "agent email", "application received", "application validated"]

        self.weeks = {}

        self.cases = {}

        self.weeks_selection = []

        self.get_week_selection()

        self.quantity_of_cases = {}

        self.weeks_results = {}


        self.csv_file = self.borough_name + ".csv"

        self.weeks = {}

        self.done_case = []

        self.get_week_selection()

        #self.write_header()

        self.failed_cases = []

        self.load_cases_data_from_json()

        if os.path.exists(self.csv_file) == False:
            self.write_header()
        
        self.get_done_case_numbers()

#weeks

    def get_week_selection(self):  
        start_search = self.s.get(self.url_start)
        s_search_soup = bs(start_search.text, "lxml")  
        weeks_soup = s_search_soup.find_all(id ="week")[0]
        for w in weeks_soup.find_all("option"):
            week = w["value"]
            if week not in self.weeks:
                self.weeks[week] = {}
                self.weeks[week]["week_complete"] = False
            self.weeks_selection.append(w["value"])
    


    #check for amount of weeks

    def search_for_week_start(self, week):

        search_start_data = {'searchCriteria.ward': '', 'week': week, 'dateType': 'DC_Validated', 'searchType': 'Application'}

        search_start = self.s.post(self.url_search_start, data = search_start_data)
        search_soup = bs(search_start.text, "lxml")
        searchResultsContainer_soup = search_soup.find_all(id = "searchResultsContainer")[0]
        try:
            total_cases_for_week = int(searchResultsContainer_soup.span.text.split(" of ")[1])
            self.weeks[week]["total_cases"] = total_cases_for_week
        except Exception:
            total_cases_for_week = len(searchResultsContainer_soup.find_all("li"))
            self.weeks[week]["total_cases"] = total_cases_for_week
       

    #Scrapes soup of all pages for search results for a week

    def scrape_weekly_search_results(self, week):
        page_number = 1
        self.weeks_results[week] = []
        total = self.weeks[week]["total_cases"]
        for page in range(0, total, 100):
            search_criteria_data = {"searchCriteria.page": page_number,"action": "page","orderBy": "DateReceived","orderByDirection": "Descending", "searchCriteria.resultsPerPage": "100"}
            next_page = self.s.post(self.url_paged_results, data = search_criteria_data)
            next_page_soup = bs(next_page.text, "lxml")
            next_page_results_soup = next_page_soup.find_all(id = "searchresults")[0].find_all("li")
            self.weeks_results[week].extend(next_page_results_soup)
            page_number += 1


    def get_cases_from_weekly_search(self, week):
        cases_added = 0
        for case in self.weeks_results[week]:
                case_number = case.find_all("p")[1].text.replace("\n", "").replace("  ", "").replace("\r", "").split("|")[0].split(":")[1]
                validated = case.find_all("p")[1].text.replace("\n", "").replace("  ", "").replace("\r", "").split("|")[2].split(":")[1]
                link = case.a["href"]
                self.cases[case_number] = {"application validated": validated, "url" : link, "refence": case_number}
                cases_added += 1
        self.weeks[week]["cases_added"] = cases_added 



    def get_cases_from_all_weeks(self):
        self.get_week_selection()
        for week in self.weeks_selection:
            self.search_for_week_start(week)
            self.scrape_weekly_search_results(week)
            self.get_cases_from_weekly_search(week)
            print(week + " added to json")
            self.update_json_file()



#CSV JSONv


    def write_header(self):
        
        try:
            with open(self.csv_file, "a") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.csv_columns)
                writer.writeheader()
        except IOError:
            print("I/O error")
        
    def overwrite_csv(self):
        try:
            with open(self.csv_file, "w") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.csv_columns)
                writer.writeheader()
        except IOError:
            print("I/O error")

    def _dict_to_csv(self, dictionary):
        try:
            with open(self.csv_file, "a") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.csv_columns)
                writer.writerow(dictionary)
        except IOError:
            print("I/O error")

    def load_cases_data_from_json(self):
        if os.path.exists("data.json") == False:
            self.update_json_file()
        else:
            with open("data.json") as j:
                    self.json_data = json.load(j)
                    try:
                        self.weeks = self.json_data[self.borough_name]["week"]
                        self.cases = self.json_data[self.borough_name]["cases"]
                    except Exception as e:
                        self.update_json_file()
                        print("Created Borough in JSON file as " + str(e))


    def update_json_file(self):
        with open("data.json", "w") as outfile:
            self.json_data[self.borough_name] = {"week": self.weeks, "cases": self.cases}
            json.dump(self.json_data, outfile)


#Check weeks

    def check_if_weekly_search_complete(self,week):
        if self.weeks[week]["total_cases"] == self.weeks[week]["cases_added"]:
            self.weeks[week]["week_complete"] = True
        else:
            self.weeks[week]["week_complete"] = False

    def check_weeks_to_do(self):
        self.weeks_to_do = []
        for week in self.weeks:
            if self.weeks[week]["week_complete"] == False:
                self.weeks_to_do.append(week)






    def scrape_case_to_csv(self, case):
        if case not in self.done_cases:
                try:
                    self.scrape_case_from_url(self.cases[case]["url"])
                except Exception:
                    if case not in self.failed_cases:
                        self.failed_cases.append(case)




    def scrape_all_cases_to_csv(self):
        for case in self.cases:
            self.scrape_case_to_csv(case)



    def scrape_cases_within_dates(self, start, end):

        df = pd.DataFrame.from_dict(self.cases, orient = "index", columns=["url", "application validated"])

        end_date = self.string_date_to_datetime(end)
        start_date = self.string_date_to_datetime(start)
        end_64 = np.datetime64(end_date)
        start_64 = np.datetime64(start_date)

        cases_in_range = df.loc[df["datetime"].between(start_64, end_64, inclusive= True)]
        case_list = cases_in_range.axes[0].tolist()

        for case in case_list:
            self.scrape_case_to_csv(case)


#Scraping Individual Cases

    def _check_header_and_scrape(self, soup, case):
        for t in range(0,len(soup)):
            header = soup[t].th.text.replace("\n", "").replace("  ", "").lower()
            value = soup[t].td.text.replace("\n", "").replace("  ", "")
            if header in self.csv_columns:
                case[header] = value
        return case



 

    def scrape_case_from_url(self, case_url):

        summary_url = self.url_for_case_base + case_url
        details_url = summary_url.replace("summary", "details")
        contacts_url = summary_url.replace("summary", "contacts")

        summary = self.s.get(summary_url)
        summary_soup = bs(summary.text, "lxml")

        case = {}
        
        summary_table = summary_soup.find_all("tr")
        

        self._check_header_and_scrape(summary_table, case)

        details = self.s.get(details_url)
        details_soup = bs(details.text, "lxml")
        details_table = details_soup.find_all("tr")
        case_number = case["reference"]

        self._check_header_and_scrape(details_table, case)
            
        contacts = self.s.get(contacts_url)
        contacts_soup = bs(contacts.text, "lxml")
        contacts_table = contacts_soup.find_all("tr")
        for a in range(0, len(contacts_table)):
            try:
                if contacts_table[a].th.text.lower() in ["phone", "phone number", "mobile nunmber", "mobile phone"]:
                    case["agent phone number"] = contacts_table[a].td.text
                if contacts_table[a].th.text.lower() in ["email", "e-mail"]:
                   case["agent email"] = contacts_table[a].td.text
            except:
                continue

        try:
            with open(self.csv_file, "a") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.csv_columns)
                writer.writerow(case)
        except IOError:
            print("I/O error")




    def check_for_new_cases_latest_week(self):
        week = self.weeks_selection[0]
        if week in self.weeks and self.weeks["week_complete"] == True:
            old_total = self.weeks[week]["total_cases"]
            self.search_for_week_start(week)
            if self.weeks[week]["cases_added"] < self.weeks[week]["total_cases"]:
                self.weeks[week]["week_complete"] = "missing some weeks"







    def string_date_to_datetime(self, string):
        if len(string) > 11:
            date = datetime.strptime(string[4:], "%d %b %Y")
        else:
            date = datetime.strptime(string, "%d %b %Y")
        return date


    def get_done_case_numbers(self):
        df = pd.read_csv(self.csv_file, skiprows=0)
        done_case_numbers = df["reference"].values
        self.done_cases = done_case_numbers


        


    def get_cases_dataframe_within_weeklimit(self, start_date, end_date):

        df = pd.DataFrame.from_dict(self.cases, orient = "index", columns=["url", "application validated"])
        df["datetime"] =  [self.string_date_to_datetime(i) for i in df["application validated"]]


        end = self.string_date_to_datetime(end_date)
        start = self.string_date_to_datetime(start_date)
        end_64 = np.datetime64(end)
        start_64 = np.datetime64(start)

        cases_in_range = df.loc[df["datetime"].between(start_64, end_64, inclusive= True)]
        case_list = cases_in_range.axes[0].tolist()

        self.case_list = case_list




    def add_new_cases(self):
        df = pd.read_csv(self.csv_file, skiprows=0)
        df["datetime"] =  [self.string_date_to_datetime(i) for i in df["application validated"]]
        last_date = df["datetime"].max()
        last_week_num = last_date.isocalendar()[1]
        weeks_to_scrape = {}
        for w in self.weeks_selection:
            w_num = datetime.strptime(w, "%d %b %Y").isocalendar()[1] 
            if w_num >= last_week_num:
                weeks_to_scrape[w] = w_num
            else:
                break

        self.new_weeks = weeks_to_scrape
        for w in weeks_to_scrape:
                self.search_for_week_start(w)
                self.scrape_weekly_search_results(w)
                self.get_cases_from_weekly_search(w)


        df = pd.DataFrame.from_dict(self.cases, orient = "index", columns=["url", "application validated"])
        df["datetime"] =  [self.string_date_to_datetime(i) for i in df["application validated"]]
        cases_in_range = df.loc[df["datetime"] >= last_date]
        case_list = cases_in_range.axes[0].tolist()
        for case in case_list:
            self.scrape_case_to_csv(case)



    def test_cases(self, date):
        df = pd.read_csv(self.csv_file, skiprows=0)
        df["datetime"] =  [self.string_date_to_datetime(i) for i in df["application validated"]]

        d = self.string_date_to_datetime(date)


        last_week_num = d.isocalendar()[1]
        weeks_to_scrape = {}

        for w in self.weeks_selection:
            w_num = datetime.strptime(w, "%d %b %Y").isocalendar()[1] 
            if w_num >= last_week_num:
                weeks_to_scrape[w] = w_num
            else:
                break
        self.test_weeks = weeks_to_scrape


