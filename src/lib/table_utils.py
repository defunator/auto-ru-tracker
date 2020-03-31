'''
tables structure:
chat_ids
row: chat_id | prices spreadsheet link | start_urls spreadsheet link

prices_{chat_id}
row: start_url(url or filter url) | url | name (car name) | price1 | price2  | ...

start_urls_{chat_id}
row: start_url
'''
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
]

credentials = ServiceAccountCredentials.from_json_keyfile_name(f'{os.getcwd()}/src/lib/credentials.json', scope)

client = gspread.authorize(credentials)
spreadsheet_link_prefix = 'https://docs.google.com/spreadsheets/d/'

def add_chat_id(chat_id):
    '''
    If {chat_id} is not logged in adds in to {chat_ids} and creates needed tables.
    Return True if new chat_id.
    '''
    chat_ids = client.open('chat_ids').sheet1

    if len(chat_ids.findall(str(chat_id))) == 0:
        prices = client.create(f'prices_{chat_id}')
        prices.share('semyonli21@gmail.com', perm_type='user', role='writer')
        start_urls = client.create(f'start_urls_{chat_id}')
        start_urls.share('semyonli21@gmail.com', perm_type='user', role='writer')

        chat_ids.append_row([chat_id,
                    f'{spreadsheet_link_prefix}{prices.id}',
                    f'{spreadsheet_link_prefix}{start_urls.id}'])
        return True
    return False

def get_chat_ids():
    '''
    Returns logged chat_ids.
    '''
    chat_ids = client.open('chat_ids').sheet1.get_all_values()
    return [int(chat_id[0]) for chat_id in chat_ids]

def update_car_price(start_url, url, name, price, chat_id):
    '''
    Tries to update car ad's price on {url}, if price didn't change - doesn't update.
    '''
    prices = client.open(f'prices_{chat_id}').sheet1
    url_row = prices.findall(url)

    if len(url_row) == 0:
        prices.append_row([start_url, url, name, price])
    else:
        row = prices.row_values(url_row[0].row)
        if int(row[-1]) != price:
            prices.update_cell(url_row[0].row, len(row) + 1, price)

def get_prices(chat_id):
    '''
    Returns prices_{chat_id} table.
    '''
    raw_prices = client.open(f'prices_{chat_id}').sheet1.get_all_values()
    prices = []

    for price in raw_prices:
        prices.append([])
        for el in price:
            if el == '':
                break
            if el.isnumeric():
                prices[-1].append('{0:,d}'.format(int(el)).replace(',', "'"))
            else:
                prices[-1].append(el)

    return prices

def add_start_url(start_url, chat_id):
    '''
    Tries to add start_url to start_urls, if already exists - doesn't add.
    '''
    start_urls = client.open(f'start_urls_{chat_id}').sheet1

    if len(start_urls.findall(start_url)) == 0:
        start_urls.append_row([start_url])

def get_start_urls(chat_id):
    '''
    Returns list of start_urls.
    '''
    start_urls = client.open(f'start_urls_{chat_id}').sheet1.get_all_values()
    return [start_url[0] for start_url in start_urls]

def delete_start_url(start_url, chat_id):
    '''
    Deletes start_url from start_urls and row with same start_url from prices.
    '''
    has_start_url = False
    start_urls = client.open(f'start_urls_{chat_id}').sheet1
    for row in start_urls.findall(start_url)[::-1]:
        has_start_url = True
        start_urls.delete_row(row.row)

    prices = client.open(f'prices_{chat_id}').sheet1
    for row in prices.findall(start_url)[::-1]:
        prices.delete_row(row.row)

    return has_start_url
