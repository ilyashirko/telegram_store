from xmlrpc.client import ResponseError
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from telegram.ext import (
    Updater,
    Filters,
    CommandHandler,
    MessageHandler,
    CallbackContext,
    CallbackQueryHandler,
    ConversationHandler
)
from redis import Redis
from environs import Env
from functools import partial
import elastic_management
import json
from textwrap import dedent
import requests

DEFAULT_REDIS_HOST = 'localhost'

DEFAULT_REDIS_PORT = 6379

DEFAULT_REDIS_PASSWORD = None

DEFAULT_REDIS_DB = 0

RETURN_INLINE_KEYBOARD = InlineKeyboardMarkup(
    [[InlineKeyboardButton(text='Назад', callback_data='main_menu')]]
)

def main_menu(update: Update,
              context: CallbackContext) -> str:
    token = elastic_management.get_token(env.str('CLIENT_ID'))
    products = elastic_management.get_products(token)
    if update.callback_query:
        context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=update.callback_query.message.message_id,
        )
    buttons = list()
    for product in products['data']:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=product['attributes']['name'],
                    callback_data=f'product:{product["id"]}'
                )
            ]
        )
    context.bot.send_message(
        update.effective_chat.id,
        'Please choose:',
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return 'HANDLE_MENU'


def handle_menu(update: Update,
                context: CallbackContext) -> str:
    _, product_id = update.callback_query.data.split(':')
    token = elastic_management.get_token(env.str('CLIENT_ID'))
    product = elastic_management.get_product(token, product_id)
    response = requests.get(product['included']['main_images'][0]['link']['href'])
    context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=response.content,
        caption=dedent(
            f"""
            {product['data']['attributes']['name']}

            {product['data']['attributes']['description']}

            {product['data']['attributes']['price']['USD']['amount'] / 100} USD
            """
        ),
        reply_markup=RETURN_INLINE_KEYBOARD
    )
    context.bot.delete_message(
        chat_id=update.effective_chat.id,
        message_id=update.callback_query.message.message_id,
    )
    return 'HANDLE_DESCRIPTION'



if __name__ == '__main__':
    env = Env()
    env.read_env()

    redis = Redis(
        host=env.str('REDIS_HOST', DEFAULT_REDIS_HOST),
        port=env.int('REDIS_PORT', DEFAULT_REDIS_PORT),
        password=env.str('REDIS_PASSWORD', DEFAULT_REDIS_PASSWORD),
        db=env.int('REDIS_DB', DEFAULT_REDIS_DB)
    )

    updater = Updater(token=env.str('TELEGRAM_BOT_TOKEN'), use_context=True)

    updater.dispatcher.add_handler(
        ConversationHandler(
            entry_points = [
                CommandHandler('start', main_menu)
            ],
            states = {
                'HANDLE_MENU': [
                    CallbackQueryHandler(callback=handle_menu, pattern='product')
                ],
                'HANDLE_DESCRIPTION': [
                    CallbackQueryHandler(callback=main_menu, pattern='main_menu')
                ]
            },
            fallbacks=[]
        )
    )
    



    updater.start_polling()
    updater.idle()
