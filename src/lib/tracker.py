from bs4 import BeautifulSoup
from lxml import etree as et
import json
import os
import re
import requests
import time

import lib.table_utils as table_utils

requests.adapters.DEFAULT_RETRIES = 5

class PriceTracker():
    def __init__(self, chat_id, start_urls=None):
        self.start_urls = start_urls
        if start_urls == None:
            self.start_urls = table_utils.get_start_urls(chat_id)
        self.chat_id = chat_id

    def start_requests(self):
        for url in self.start_urls:
            if '?' not in url:
                response = requests.get(url)
                time.sleep(0.13)
                self.parse_car_url(response, url, url)
            else:
                for page in range(1, 5):
                    base_url = f'{url}&page={page}'
                    response = requests.get(base_url)
                    time.sleep(0.13)
                    self.parse_filter_url(response, url)


    def parse_car_url(self, response, url, base_url):
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            car_info = et.HTML(str(soup.find_all('div', {'data-bem': re.compile('{"sale-data-attributes".*}')})[0]))
            car_info = car_info.getchildren()[0].getchildren()[0].get('data-bem')
            car_info = json.loads(car_info)['sale-data-attributes']
            price = car_info['price']
            markName = car_info['markName']
            modelName = car_info['modelName']
            name = f'{markName} {modelName}'
            table_utils.update_url(url, base_url, price, name, self.chat_id)
        except:
            print('parse_car_url fail')

    def parse_filter_url(self, response, base_url):
        soup = BeautifulSoup(response.text, 'html.parser')
        for url_tag in soup.find_all('a', {'class': 'Link ListingItemThumb'}):
            url = et.HTML(str(url_tag)).getchildren()[0].getchildren()[0].get('href')
            response = requests.get(url)
            time.sleep(0.13)
            self.parse_car_url(response, url, base_url)

