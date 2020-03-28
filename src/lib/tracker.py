import requests
from bs4 import BeautifulSoup
from lxml import etree as et
import re
import os
import json
import lib.table_utils as table_utils

requests.adapters.DEFAULT_RETRIES = 5
PRICE_TRACKER_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36'
}

class PriceTracker():
    def __init__(self, chat_id, start_urls=None):
        self.start_urls = start_urls
        if start_urls == None:
            self.start_urls = table_utils.get_start_urls(chat_id)
        self.chat_id = chat_id
        self.session = requests.Session()
        self.session.headers.update(PRICE_TRACKER_HEADERS)

    def start_requests(self):
        for url in self.start_urls:
            if '?' not in url:
                response = self.session.get(url, timeout=1.23)
                self.parse_car_url(response, url, url)
            else:
                for page in range(1, 3):
                    base_url = f'{url}&page={page}'
                    response = self.session.get(base_url, timeout=1.23)
                    self.parse_filter_url(response, base_url)


    def parse_car_url(self, response, url, base_url):
        print(f'parse_car_url {url}')
        soup = BeautifulSoup(response.text, 'html.parser')
        car_info = et.HTML(str(soup.find_all('div', {'data-bem': re.compile('{"sale-data-attributes".*}')})[0]))
        car_info = car_info.getchildren()[0].getchildren()[0].get('data-bem')
        car_info = json.loads(car_info)['sale-data-attributes']
        price = car_info['price']
        markName = car_info['markName']
        modelName = car_info['modelName']
        name = f'{markName} {modelName}'
        table_utils.update_url(url, base_url, price, name, self.chat_id)

    def parse_filter_url(self, response, base_url):
        print(f'parse_filter_url {base_url}')
        soup = BeautifulSoup(response.text, 'html.parser')
        for url_tag in soup.find_all('a', {'class': 'Link ListingItemThumb'}):
            url = et.HTML(str(url_tag)).getchildren()[0].getchildren()[0].get('href')
            response = self.session.get(url, timeout=1.23)
            self.parse_car_url(response, url, base_url)

