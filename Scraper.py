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

        self.url_search_advanced = self.url_base + "/search.do?action=advanced"

        self.url_results_advanced = self.url_base + '/advancedSearchResults.do?action=firstPage'

        self.s = requests.Session()

        self.csv_columns = ["reference", "alternative reference", "address", "proposal", "status", "applicant name", "agent name", "agent address", "agent phone number", "agent email", "application received", "application validated", "decision issued data", "decision"]

        self.weeks = {}

        self.cases = {}

        self.weeks_selection = []

        self.get_week_selection()

        self.quantity_of_cases = {}

        self.weeks_results = {}

        self.csv_file = self.borough_name + ".csv"

        self.excel_file = self.borough_name + ".xlsx"

        self.done_case = []

        self.date_symbol = "/"

        self.search_scrape_failed_cases = []

        self.get_week_selection()

        self.failed_cases = []

        self.load_cases_data_from_json()

        if os.path.exists(self.csv_file) == False:
            self.write_header()

        print("ready!")
        


#weeks scraping can be combined

    def get_week_selection(self):  
        start_search = self.s.get(self.url_start)
        s_search_soup = bs(start_search.text, "lxml")  
        weeks_soup = s_search_soup.find_all(id ="week")[0]
        for w in weeks_soup.find_all("option"):
            week = w["value"]
            if week not in self.weeks:
                self.weeks[week] = {}
                self.weeks[week] = {"week_complete" : False, "total_cases" : None, "cases_added" : 0}
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
            try:
                case_number = case.find_all("p")[1].text.replace("\n", "").replace("  ", "").replace("\r", "").split("|")[0].split(":")[1]
                validated = case.find_all("p")[1].text.replace("\n", "").replace("  ", "").replace("\r", "").split("|")[2].split(":")[1]
                link = case.a["href"]
                self.cases[case_number] = {"application validated": validated, "url" : link, "refence": case_number}
                cases_added += 1
            except:
                self.search_scrape_failed_cases.append(case)
        self.weeks[week]["cases_added"] = cases_added
        self.check_if_weekly_search_complete(week)







#CSV JSON Excel


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


            

    def csv_to_excel(self):
        for self.csv_file in glob.glob(os.path.join('.', '*.csv')):
                workbook = Workbook(self.csv_file[:-4] + '.xlsx')
                worksheet = workbook.add_worksheet()
                red = workbook.add_format()
                red.set_bg_color("#FF0000")
                green = workbook.add_format()
                green.set_bg_color('#008000')
                yellow = workbook.add_format()
                yellow.set_bg_color('#FFFF00')
                with open(self.csv_file, 'rt') as f:
                    reader = csv.reader(f)
                    for r, row in enumerate(reader):
                        for c, col in enumerate(row):
                            worksheet.write(r, c, col)
                worksheet.write_row("A1:E1", self.csv_columns[0:5], red)
                worksheet.write_row("F1:J1", self.csv_columns[5:10], green)
                worksheet.write_row("K1:N1", self.csv_columns[10:], yellow)
                workbook.close()



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



#Scrape Cases Mode

    


    def get_cases_from_all_weeks(self):
        self.get_week_selection()
        for week in self.weeks_selection:
            self.check_if_weekly_search_complete(week)
            if self.weeks[week]["week_complete"] == False:
                self.search_for_week_start(week)
                self.scrape_weekly_search_results(week)
                self.get_cases_from_weekly_search(week)
                print(week + " added to json")
                self.update_json_file()
        for case in self.cases:
            self.scrape_case_to_csv(case)



    def add_new_cases(self):
        self.get_latest_done_date()
        self.scrape_search_within_dates(self.string_latest_date, self.string_today)



    def scrape_search_within_dates(self, start, end):

        search = self.s.get(self.url_search_advanced)
        start = self.convert_date(start)
        end = self.convert_date(end)
        self.search_results = []

        search_start_data = {'date(applicationValidatedStart)': start, 'date(applicationValidatedEnd)': end, 'searchType': 'Application'}
        search_start = self.s.post(self.url_search_start, data = search_start_data)
        search_soup = bs(search_start.text, "lxml")
        searchResultsContainer_soup = search_soup.find_all(id = "searchResultsContainer")[0]
        total_of = searchResultsContainer_soup.span.text
        if total_of != None:
            total_cases_for_search = int(total_of.split(" of ")[1])
        else:
            total_cases_for_search = len(searchResultsContainer_soup.find_all("li"))
        
        total = total_cases_for_search
        page_number = 1
        self.get_done_cases_search_period(start, end)
        for page in range(0, total, 100):
            search_criteria_data = {"searchCriteria.page": page_number,"action": "page","orderBy": "DateReceived","orderByDirection": "Descending", "searchCriteria.resultsPerPage": "100"}
            next_page = self.s.post(self.url_paged_results, data = search_criteria_data)
            next_page_soup = bs(next_page.text, "lxml")
            next_page_results_soup = next_page_soup.find_all(id = "searchresults")[0].find_all("li")
            self.search_results.extend(next_page_results_soup)
            page_number += 1

        self.get_done_cases_search_period(start, end)
        for case in self.search_results:
            try:
                case_number = case.find_all("p")[1].text.replace("\n", "").replace("  ", "").replace("\r", "").split("|")[0].split(":")[1]
                link = case.a["href"]
                if case_number not in self.search_done_cases:
                    try:
                        self.scrape_case_from_url(link)
                    except Exception:
                        if case not in self.failed_cases:
                            self.failed_cases.append(case)
            except:
                self.search_scrape_failed_cases.append(case)





#Scraping Individual Cases

    def _check_header_and_scrape(self, soup, case):
        for t in range(0,len(soup)):
            header = soup[t].th.text.replace("\n", "").replace("  ", "").lower()
            value = soup[t].td.text.replace("\n", "").replace("  ", "")
            if header in self.csv_columns:
                case[header] = value
        return case



    def scrape_case_to_csv(self, case):
        self.get_done_case_numbers()
        if case not in self.done_cases:
                try:
                    self.scrape_case_from_url(self.cases[case]["url"])
                except Exception:
                    if case not in self.failed_cases:
                        self.failed_cases.append(case)

 

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



# DATETIME 



    def string_date_to_datetime(self, string):
        if "-" in string:
            string = string.replace("-", " ")
        if "_" in string:
            string = string.replace("_", " ")
        if "/" in string:
            string = string.replace("/", " ")

        if string.replace(" ","").isdigit():

            date = datetime.strptime(string, "%d-%m-%Y")
        elif len(string) > 11:
            date = datetime.strptime(string[4:], "%d %b %Y")
        else:
            date = datetime.strptime(string, "%d %b %Y")
        return date


    def convert_date(self,date):
        symbols = ("_", "/", "-", ".", ",","|","\\")
        s = self.date_symbol
        old_s = [s for s in symbols if (s in date)][0]
        date = date.replace(old_s, s)   
        if date.replace(s, "").isdigit() == False:
            d = date.split(s)
            if len(d[1]) == 3:
                month = datetime.strptime(d[1],"%b").month 
            else:
                month = datetime.strptime(d[1],"%B").month 
            date = d[0] + s  + str(month).zfill(2) + s +  d[2]
        return date 
    
    
# Data from Excel


    def get_done_case_numbers(self):
        df = pd.read_excel(self.excel_file, skiprows=0)
        df = df.dropna(how = "all").reset_index().drop(["index"], axis = 1)
        self.done_cases = df["reference"].values

    def get_done_cases_search_period(self,start, end):
        df = pd.read_excel(self.excel_file, skiprows=0)
        df = df.dropna(how = "all").reset_index().drop(["index"], axis = 1)
        df["datetime"] =  [self.string_date_to_datetime(i) for i in df["application validated"]]
        s = self.date_symbol

        start = self.convert_date(start)
        end = self.convert_date(end)
        start = datetime.strptime(start, "%d" + s + "%m" + s +  "%Y")
        end = datetime.strptime(end, "%d" + s + "%m" + s +"%Y")
        df2 =  df[df["datetime"].between(e,s, inclusive = True)]["reference"].reset_index().drop(["index"],axis=1)
        self.search_done_cases = df2.values



    def get_latest_done_date(self):
        df = pd.read_excel(self.excel_file, skiprows=0)
        df = df.dropna(how = "all").reset_index().drop(["index"], axis = 1)
        df["datetime"] =  [self.string_date_to_datetime(i) for i in df["application validated"]]
        self.datetime_latest_date = df["datetime"].max()
        s = self.date_symbol
        self.string_latest_date =  self.datetime_latest_date.strftime("%d" + s + "%m" + s  +"%Y")
        self.string_today = datetime.now().strftime("%d" + s + "%m" + s +"%Y")
