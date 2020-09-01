import requests
from bs4 import BeautifulSoup as bs
import csv
from scraper import Scraper
import json


edinburgh = Scraper("Edinburgh")
edinburgh.scrape_everything()

