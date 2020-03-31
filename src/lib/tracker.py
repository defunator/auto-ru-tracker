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
    '''
    Main class that parses urls and updates its price tags
    '''
    def __init__(self, chat_id, start_urls=None):
        self.start_urls = start_urls
        if start_urls == None:
            self.start_urls = table_utils.get_start_urls(chat_id)
        self.chat_id = chat_id

    def start_requests(self):
        '''
        Starts start_urls parsing
        '''
        for url in self.start_urls:
            if '?' not in url:
                response = requests.get(url)
                time.sleep(1.23)
                self.parse_car_url(response, url, url)
            else:
                for page in range(1, 5):
                    if 'auto.ru' in url:
                        base_url = f'{url}&page={page}'
                    else:
                        base_url = f'{url}&p={page}'
                    response = requests.get(base_url)
                    time.sleep(1.23)
                    self.parse_filter_url(response, url)

    def auto_ru_parse_url(self, response):
        '''
        Parse auto.ru ad(of single car).
        '''
        soup = BeautifulSoup(response.text, 'html.parser')
        car_info = et.HTML(str(soup.find_all('div', {'data-bem': re.compile('{"sale-data-attributes".*}')})[0]))
        car_info = car_info.getchildren()[0].getchildren()[0].get('data-bem')
        car_info = json.loads(car_info)['sale-data-attributes']
        price = car_info['price']
        markName = car_info['markName']
        modelName = car_info['modelName']
        name = f'{markName} {modelName}'

        return name, price

    def avito_parse_url(self, response):
        '''
        Parse avito.ru/.*?/avtomibili ad(of single car)
        '''
        car_info = re.search(r'<script>\n window.dataLayer = \[(.*?)\];', response.text).group(1)
        car_info = json.loads(car_info.split('},')[1])
        price = car_info['itemPrice']
        brandName = car_info['brand']
        modelName = car_info['model']
        name = f'{brandName} {modelName}'

        return name, price

    def parse_car_url(self, response, start_url, url):
        '''
        Parse ad of single car and update price tag
        '''
        try:
            if 'auto.ru' in url:
                name, price = self.auto_ru_parse_url(response)
            else:
                name, price = self.avito_parse_url(response)
            table_utils.update_car_price(start_url, url, name, price, self.chat_id)
        except:
            print(f'ERROR: parse_car_url {url}')

    def auto_ru_parse_filter(self, response):
        '''
        Parse auto.ru filter url
        Returt a list of ad urls
        '''
        soup = BeautifulSoup(response.text, 'html.parser')
        urls_tag = soup.find_all('a', {'class': 'Link ListingItemThumb'})
        urls = []

        for url_tag in urls_tag:
            url = et.HTML(str(url_tag)).getchildren()[0].getchildren()[0].get('href')
            urls.append(url)

        return urls

    def avito_parse_filter(self, response):
        '''
        Parse avito filter url
        Return a list of ad urls
        '''
        urls_suf = re.findall(r'<a class="snippet-link"\n itemprop="url"\n href="(.*?)"', response.text)
        urls = []

        for url_suf in urls_suf:
            urls.append(f'https://www.avito.ru{url_suf}')

        return urls


    def parse_filter_url(self, response, start_url):
        '''
        Parse filter url and start ad url parsing
        '''
        try:
            if 'auto.ru' in start_url:
                urls = self.auto_ru_parse_filter(response)
            else:
                urls = self.avito_parse_filter(response)

            for url in urls:
                response = requests.get(url)
                time.sleep(1.23)
                self.parse_car_url(response, start_url, url)
        except:
            print(f'ERROR: parse_filter_url {start_url}')

