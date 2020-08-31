import requests
from bs4 import BeautifulSoup as bs
import csv
import json
from datetime import datetime, date, time
import numpy as np
import pandas as pd
from os import path
import os.path


{'Applicant Name', 'Agent Name', 'Agent Address', 'Proposal', 'M3 Unique Case No' , 'Date Received', 'Decision Date', 'Premises Address', 'Application Address', 'Case No', 'Alternative Ref','Registered Date'}


class Harrow():

    def __init__(self):

        self.borough_name = "Harrow"

        self.s = requests.Session()

        self.weeks = {}

        self.cases = {}

        self.csv_file = self.borough_name + ".csv"

        self.weeks = {}

        self.csv_columns = ['Applicant Name', 'Agent Name', 'Agent Address', 'Proposal', 'M3 Unique Case No' , 'Date Received', 'Decision Date', 'Premises Address', 'Application Address', 'Case No', 'Alternative Ref','Registered Date']

        #self.write_header()

        self.load_cases_data_from_json()

        if os.path.exists(self.csv_file) == False:
            self.write_header()


        self.data =  {'refType': 'GFPlanning', 'fromRow': 1, 'toRow': 1, 'keyNumb': '10', 'keyText': 'Subject'}
        self.url = 'https://planningsearch.harrow.gov.uk/civica/Resource/Civica/Handler.ashx/keyobject/search'
        self.labels = ['Alternative Reference', 'Applicant Name', 'Agent Name', 'Agent Address', 'Agent Phone', 'Agent Email', 'Agent Email Address' 'Application Received', 'Application Validated', 'Reference', 'Address', 'Proposal', 'Status', "Registered Date", 'Case No', 'M3 Unique Case No', 'Premises Address', "Date Received", 'Application Address', 'Alternative Ref', 'Decision Date']


    def scrape_case(self, num):
        data = {'refType': 'GFPlanning', 'fromRow': 1, 'toRow': 1, 'keyNumb': num , 'keyText': 'Subject'}
        r = self.s.post(self.url, data)
        response_json = r.json()
        cases_done = 0
        if  r.status_code == 200 and len(r.json()) > 0:
            j = response_json[0]["Items"]
            case = {}
            for i in range(len(j)):
                if j[i]["Label"] in self.labels: 
                    label = j[i]["Label"] 
                    value = j[i]["Value"]
                    case[label] = value
            self._dict_to_csv(case)
            cases_done += 1
            if cases_done % 25 == 0:
                print("Done:" + cases_done)


    def try_all(self):
        for n in range(930000, 950000):
            try:
                self.scrape_case(n)
            except:
                continue
            



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
        with open("data.json") as j:
            self.json_data = json.load(j)
            try:
                self.weeks = self.json_data[self.borough_name]["week"]
                self.cases = self.json_data[self.borough_name]["cases"]
                
            except Exception as e:
                self.json_data[self.borough_name] = {"week": self.weeks, "cases": self.cases}
                print("Created Borough in JSON file as " + str(e))

    def update_json_file(self):
        with open("data.json", "w") as outfile:
            self.json_data[self.borough_name] = {"week": self.weeks, "cases": self.cases}
            json.dump(self.json_data, outfile)