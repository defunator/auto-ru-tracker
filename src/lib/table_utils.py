import os
import pandas as pd


def update_url(url, base_url, price, name, chat_id):
    if not os.path.exists('data'):
        os.makedirs('data')
    if not os.path.exists(f'./data/{chat_id}'):
        os.makedirs(f'./data/{chat_id}')

    if os.path.exists(f'./data/{chat_id}/prices'):
        prices = pd.read_csv(f'./data/{chat_id}/prices')
        if url in prices.url.values:
            prices_list = prices.loc[prices.url == url, 'prices'][0]
            if str(prices_list).split('|')[-1] != str(price):
                prices.loc[prices.url == url, 'prices'] = f'{prices_list}|{price}'
        else:
            prices.loc[prices.shape[0]] = [base_url, url, name, price]
    else:
        prices = pd.DataFrame({'base_url': [base_url],
                               'url': [url],
                               'name': [name],
                               'prices': [price]})

    prices.to_csv(f'./data/{chat_id}/prices', index=False)

def get_start_urls(chat_id):
    if os.path.exists(f'./data/{chat_id}/start_urls'):
        start_urls = pd.read_csv(f'./data/{chat_id}/start_urls')
        return list(start_urls.url)
    return []

def add_start_url(url, chat_id):
    if not os.path.exists('data'):
        os.makedirs('data')
    if not os.path.exists(f'./data/{chat_id}'):
        os.makedirs(f'./data/{chat_id}')

    if os.path.exists(f'./data/{chat_id}/start_urls'):
        start_urls = pd.read_csv(f'./data/{chat_id}/start_urls')
        if url not in start_urls.url.values:
            start_urls.loc[start_urls.shape[0]] = [url]
    else:
        start_urls = pd.DataFrame({'url': [url]})

    start_urls.to_csv(f'./data/{chat_id}/start_urls', index=False)

def delete_start_url(url, chat_id):
    if not os.path.exists(f'./data/{chat_id}/prices'):
        return 0
    if not os.path.exists(f'./data/{chat_id}/start_urls'):
        return 0

    start_urls = pd.read_csv(f'./data/{chat_id}/start_urls', index_col=0)
    prices = pd.read_csv(f'./data/{chat_id}/prices', index_col=0)

    if url in start_urls.index and url in prices.index:
        start_urls.drop([url], inplace=True)
        prices.drop([url], inplace=True)
        return True

    return False

def get_prices(chat_id):
    if not os.path.exists(f'./data/{chat_id}/prices'):
        return pd.DataFrame()
    prices = pd.read_csv(f'./data/{chat_id}/prices')
    prices.prices = prices.prices.apply(lambda x: str(x).split('|'))
    return prices



