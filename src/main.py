import logging
from telegram.ext import (Updater, CommandHandler, MessageHandler,
                        Filters, ConversationHandler, CallbackQueryHandler)
from telegram import ParseMode
from twisted.internet import reactor
import re

from lib.tracker import PriceTracker
import lib.table_utils as table_utils
from lib.tokens import TOKEN

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

ADD_URL = range(1)
DELETE_URL = range(1)

def start(update, context):
    update.message.reply_text('''
    /start - start or update bot
    /help - help
    /add_url - add car url or filter url
    /delete_url - delete car url or filter url
    /list_url - list tracked urls
    /get_prices - list tracked car urls
    Prices are updated every hour.
    For any questions and bugs please contact @defunator.
    ''')
    context.job_queue.run_repeating(update_urls, interval=60*60, first=0, context=update.message.chat_id)


def help(update, context):
    update.message.reply_text('''
    /start - start or update bot
    /help - help
    /add_url - add car url or filter url
    /delete_url - delete car url or filter url
    /list_url - list tracked urls
    /get_prices - list tracked car urls
    Prices are updated every hour.
    For any questions and bugs please contact @defunator.
    ''')

def add_url(update, context):
    update.message.reply_text('Enter auto.ru url you want to track.')
    return ADD_URL

def add_url_input(update, context):
    url = update.message.text
    if url[:16] !=  'https://auto.ru/':
        update.message.reply_text(f'Oops, failed to track {url}!', disable_web_page_preview=True)
    chat_id = update.message.chat_id

    update.message.reply_text(f'Wait...')
    price_tracker = PriceTracker(start_urls=[url], chat_id=chat_id)
    price_tracker.start_requests()
    if price_tracker.no_errors:
        table_utils.add_start_url(url, chat_id)
        update.message.reply_text(f'Added {url}', disable_web_page_preview=True)
    else:
        update.message.reply_text(f'Oops, failed to track {url}!', disable_web_page_preview=True)

    return ConversationHandler.END

def list_urls(update, context):
    chat_id = update.message.chat_id
    repl = "Here are urls you're tracking:"
    no_urls = True

    for url in table_utils.get_start_urls(chat_id):
        no_urls = False
        repl = f'{repl}\n{url}'

    if no_urls:
        update.message.reply_text('No urls are tracked, add via /add_url.')
    else:
        update.message.reply_text(repl, disable_web_page_preview=True)

def delete_url(update, context):
    update.message.reply_text('Enter auto.ru url you want to stop tracking.')
    return DELETE_URL

def delete_url_input(update, context):
    chat_id = update.message.chat_id
    
    if not table_utils.delete_start_url(update.message.text, chat_id):
        update.message.reply_text('Oops, no such url is tracked! Check out tracked urls via /list_urls.')
    else:
        update.message.reply_text(f'Deleted {update.message.text}', disable_web_page_preview=True)

    return ConversationHandler.END

def get_prices(update, context):
    chat_id = update.message.chat_id
    resp = 'Here are price changes history:'
    has_prices = False

    for index, row in table_utils.get_prices(chat_id).iterrows():
        has_prices = True
        car_prices = '->'.join(list(map(lambda x: '{0:,d}'.format(int(x)), row['prices'])))
        car_url = row['url']
        car_name = row['name']
        resp = f'{resp}\n<a href="{car_url}">{car_name}</a>: {car_prices}'

    if has_prices:
        update.message.reply_html(resp, disable_web_page_preview=True)
    else:
        update.message.reply_text('No urls are tracked, you can add url via /add_url.')

def update_urls(context):
    chat_id = context.job.context
    prev_rows_size = []

    for index, row in table_utils.get_prices(chat_id).iterrows():
        prev_rows_size.append(len(row['prices']))

    PriceTracker(chat_id=chat_id).start_requests()

    rows = table_utils.get_prices(chat_id)
    smth_changed = False
    resp = 'These ads has changed:'

    for i in range(rows.shape[0]):
        clipped_row = rows.loc[i]['prices']
        if len(clipped_row) != prev_rows_size[i]:
            smth_changed = True
            car_prices = '->'.join(list(map(lambda x: '{0:,d}'.format(int(x)), clipped_row)))
            car_url = rows.loc[i]['url']
            car_name = rows.loc[i]['name']
            resp = f'{resp}\n<a href="{car_url}">{car_name}</a>: {car_prices}'

    if smth_changed:
        context.bot.send_message(chat_id=chat_id, text=resp, disable_web_page_preview=True, parse_mode=ParseMode.HTML)

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
        states={
            ADD_URL: [
                MessageHandler(filters=Filters.all, callback=add_url_input)
            ] 
        },
        fallbacks=[CommandHandler("add_url", add_url)]
    ))
    dp.add_handler(ConversationHandler(
        entry_points=[CommandHandler("delete_url", delete_url)],
        states={
            DELETE_URL: [
                MessageHandler(filters=Filters.all, callback=delete_url_input)
            ] 
        },
        fallbacks=[CommandHandler("add_url", delete_url)]
    ))
    dp.add_error_handler(error)

    updater.start_polling()

    updater.idle()
