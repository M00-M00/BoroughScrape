import requests
from bs4 import BeautifulSoup as bs
import csv
from scraper import Scraper
import json


barnet = Scraper("Barnet")
barnet.scrape_everything()

