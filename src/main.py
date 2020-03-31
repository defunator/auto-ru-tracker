from telegram import ParseMode
from telegram.ext import (Updater, CommandHandler, MessageHandler,
                        Filters, ConversationHandler, CallbackQueryHandler)
from twisted.internet import reactor
import logging
import re

from lib.tokens import TOKEN
from lib.tracker import PriceTracker
import lib.table_utils as table_utils

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

ADD_URL = range(1)
DELETE_URL = range(1)
UPDATE_INTERVAL = 5 * 60 * 60 # update every 5 hours
MAX_LINKS_PER_MESSAGE = 50 # if more telegram does't display links

def update_prices(context):
    '''
    Updates prices for chat_id(pass it by context.job.context)
    and sends notification on changes.
    '''
    chat_id = context.job.context
    prev_rows_size = []

    for row in table_utils.get_prices(chat_id):
        prev_rows_size.append(len(row))

    PriceTracker(chat_id=chat_id).start_requests()

    rows = table_utils.get_prices(chat_id)
    resp = 'These ads has changed:'
    resps = []

    for i in range(len(rows)):
        if len(rows[i]) != prev_rows_size[i]:
            smth_changed = True
            car_prices = '->'.join(rows[i][3:])
            car_url = rows[i][1]
            car_name = rows[i][2].encode('latin1').decode('utf8')
            resps.append((int(rows[i][-1].replace("'", '')), f'<a href="{car_url}">{car_name}</a>: {car_prices}'))

    if len(resps) != 0:
        resps.sort(reverse=True)
        links_per_message = 0
        for response in resps:
            resp = f'{resp}\n{response[1]}'
            links_per_message += 1
            if links_per_message == MAX_LINKS_PER_MESSAGE:
                context.bot.send_message(chat_id=chat_id, text=resp, disable_web_page_preview=True, parse_mode=ParseMode.HTML)
                resp, links_per_message = '', 0
        if links_per_message != 0:
            context.bot.send_message(chat_id=chat_id, text=resp, disable_web_page_preview=True, parse_mode=ParseMode.HTML)

def start(update, context):
    update.message.reply_html('''
/start - start or update bot
/help - help
/add_url - add car url or filter url
/delete_url - delete car url or filter url
/list_urls - list tracked urls
/get_prices - list tracked car urls
Prices are updated every 5 hours.
For any questions and bugs please contact @defunator.
Source: <a href="https://github.com/defunator/auto-ru-tracker">github</a>
    ''', disable_web_page_preview=True)

    chat_id = update.message.chat_id
    if table_utils.add_chat_id(chat_id):
        context.job_queue.run_repeating(update_prices, interval=UPDATE_INTERVAL, first=0, context=chat_id)

def help(update, context):
    update.message.reply_html('''
/start - start or update bot
/help - help
/add_url - add car url or filter url
/delete_url - delete car url or filter url
/list_urls - list tracked urls
/get_prices - list tracked car urls
Prices are updated every 5 hours.
For any questions and bugs please contact @defunator.
Source: <a href="https://github.com/defunator/auto-ru-tracker">github</a>
    ''', disable_web_page_preview=True)

def add_url(update, context):
    update.message.reply_text('Enter auto.ru url you want to track.')
    return ADD_URL

def add_url_input(update, context):
    '''
    Adds url to chat_id's tracked urls and tracks it once.
    '''
    url = update.message.text
    if url[:16] !=  'https://auto.ru/':
        update.message.reply_text(f'Oops, failed to track {url}! May be url is wrong. It should start with "https://auto.ru/"', disable_web_page_preview=True)
        return ConversationHandler.END
        
    chat_id = update.message.chat_id

    update.message.reply_text(f'Wait...')
    PriceTracker(start_urls=[url], chat_id=chat_id).start_requests()
    
    table_utils.add_start_url(url, chat_id)
    update.message.reply_text(f'Added {url}', disable_web_page_preview=True)

    return ConversationHandler.END

def list_urls(update, context):
    '''
    Lists all chat_id's tracked start_urls.
    '''
    chat_id = update.message.chat_id
    resp = "Here are urls you're tracking:"
    no_urls = True

    links_per_message = 0
    for url in table_utils.get_start_urls(chat_id):
        no_urls = False
        links_per_message += 1
        resp = f'{resp}\n{url}'
        if links_per_message == MAX_LINKS_PER_MESSAGE:
            update.message.reply_text(resp, disable_web_page_preview=True)
            resp, links_per_message = '', 0


    if no_urls:
        update.message.reply_text('No urls are tracked, add via /add_url.')
    elif links_per_message != 0:
        update.message.reply_text(resp, disable_web_page_preview=True)

def delete_url(update, context):
    list_urls(update, context)
    update.message.reply_text('Enter auto.ru url you want to stop tracking.')
    return DELETE_URL

def delete_url_input(update, context):
    '''
    Deletes chat_id's start_url.
    '''
    chat_id = update.message.chat_id
    
    if not table_utils.delete_start_url(update.message.text, chat_id):
        update.message.reply_text('Oops, no such url is tracked! Check out tracked urls via /list_urls.')
    else:
        update.message.reply_text(f'Deleted {update.message.text}', disable_web_page_preview=True)

    return ConversationHandler.END

def get_prices(update, context):
    '''
    Lists all chat_id's tracked ads in descending order.
    '''
    chat_id = update.message.chat_id
    resp = 'Here are price changes history:'
    resps = []
    has_prices = False

    for row in table_utils.get_prices(chat_id):
        has_prices = True
        car_prices = '->'.join(row[3:])
        car_url = row[1]
        car_name = row[2].encode('latin1').decode('utf8')
        resps.append((int(row[-1].replace("'", '')), f'<a href="{car_url}">{car_name}</a>: {car_prices}'))

    if has_prices:
        resps.sort(reverse=True)
        links_per_message = 0
        for response in resps:
            resp = f'{resp}\n{response[1]}'
            links_per_message += 1
            if links_per_message == MAX_LINKS_PER_MESSAGE:
                update.message.reply_html(resp, disable_web_page_preview=True)
                resp, links_per_message = '', 0
        if links_per_message != 0:
            update.message.reply_html(resp, disable_web_page_preview=True)
    else:
        update.message.reply_text('No urls are tracked, you can add url via /add_url.')

def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)


if __name__ == '__main__':
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("list_urls", list_urls))
    dp.add_handler(CommandHandler("get_prices", get_prices))
    dp.add_handler(ConversationHandler(
        entry_points=[CommandHandler("add_url", add_url)],
        states={ADD_URL: [MessageHandler(filters=Filters.all, callback=add_url_input)]},
        fallbacks=[CommandHandler("add_url", add_url)]
        )
    )
    dp.add_handler(ConversationHandler(
        entry_points=[CommandHandler("delete_url", delete_url)],
        states={DELETE_URL: [MessageHandler(filters=Filters.all, callback=delete_url_input)]},
        fallbacks=[CommandHandler("add_url", delete_url)]
        )
    )
    dp.add_error_handler(error)

    # Restart updating for logged chat_ids aftert restart
    for chat_id in table_utils.get_chat_ids():
        updater.job_queue.run_repeating(update_prices, interval=UPDATE_INTERVAL, first=0, context=chat_id)

    updater.start_polling()

    updater.idle()
