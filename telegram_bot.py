from datetime import datetime
from inspect import Attribute
from multiprocessing.sharedctypes import Value
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

SPARE_TOKEN_CART_TIME = 300
# SPARE_TOKEN_CART_TIME is used to prevent token or cart death while current script processing.
# 300 - random value ensuring that there is enough time for script processing


class ExpirationError(Exception):
    pass


class EntityNotFound(Exception):
    pass


def get_or_create_elastic_token(redis: Redis) -> str:
    try:
        token = redis.get('ELASTIC_AUTH_TOKEN')
        if not token:
            raise EntityNotFound

        expired_at = int(redis.get('ELASTIC_AUTH_TOKEN_expires').decode('utf-8'))
        if datetime.now().timestamp() + SPARE_TOKEN_CART_TIME > expired_at:
            raise ExpirationError

        return token.decode('utf-8')

    except (EntityNotFound, ExpirationError):
        token, expired_at = elastic_management.get_token(env.str('CLIENT_ID'))
        
        redis.set('ELASTIC_AUTH_TOKEN', token)
        redis.set('ELASTIC_AUTH_TOKEN_expires', expired_at)
        
        return token


def get_or_create_cart(redis: Redis, user_tg_id: int, elastic_token: str) -> tuple[str, bool]:
    try:
        user_cart_id = redis.get(f'{user_tg_id}_cart_id')
        if not user_cart_id:
            raise EntityNotFound
        expired_at = redis.get(f'{user_tg_id}_cart_expires')
        if not expired_at:
            # it can be if redis lose "expired" record with actual cart.
            # captured while testing
            raise EntityNotFound
        if datetime.now().timestamp() + 300 > int(expired_at.decode('utf-8')):
            raise ExpirationError
        
        return user_cart_id.decode('utf-8'), False

    except (EntityNotFound, ExpirationError):
        user_cart_id, expired_at = elastic_management.create_cart(elastic_token, str(user_tg_id))
        
        redis.set(f'{user_tg_id}_cart_id', user_cart_id)
        redis.set(f'{user_tg_id}_cart_expires', expired_at)

        return user_cart_id, True


def get_current_quantity_in_cart(redis: Redis, user_tg_id: int, elastic_token: str, product_id) -> int:
    user_cart_id, is_empty = get_or_create_cart(redis, user_tg_id, elastic_token)
    if is_empty:
        return 0
    user_cart = elastic_management.get_cart(elastic_token, user_cart_id)
    for item in user_cart['included']['items']:
        if item['product_id'] == product_id:
            return item['quantity']
    return 0
    

def make_prod_inline(quantity: int = 1, product_id: str = 'null'):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(text='-', callback_data=f'reduce_quantity:{product_id}'),
                InlineKeyboardButton(text=f'{quantity}', callback_data=f'add_to_cart:{product_id}'),
                InlineKeyboardButton(text='+', callback_data=f'increase_quantity:{product_id}')
            ],
            [InlineKeyboardButton(text='Добавить в корзину', callback_data=f'add_to_cart:{product_id}')],
            [InlineKeyboardButton(text='Назад', callback_data='main_menu')]
        ]
    )

def increase_quantity(redis: Redis,
                      update: Update,
                      context: CallbackContext) -> str:
    _, product_id = update.callback_query.data.split(':')
    elastic_token = get_or_create_elastic_token(redis)

    product_stock = elastic_management.get_product_stock(elastic_token, product_id)
    available_pcs = product_stock['data']['available']

    quantity_in_cart = get_current_quantity_in_cart(redis, update.effective_chat.id, elastic_token, product_id)
    current_quantity = int(update.callback_query.message.reply_markup['inline_keyboard'][0][1]['text'])


    if current_quantity + quantity_in_cart < available_pcs:
        context.bot.edit_message_reply_markup(
            chat_id=update.effective_chat.id,
            message_id=update.callback_query.message.message_id,
            reply_markup=make_prod_inline(quantity=(current_quantity + 1), product_id=product_id)
        )
    else:
        message = str()

        if quantity_in_cart:
            message += f'You already added {quantity_in_cart} pcs to you cart.\n\n'

        message += f'You can purchase only {available_pcs} psc.'

        context.bot.send_message(
            update.effective_chat.id,
            message
        )
    return 'HANDLE_DESCRIPTION'


def reduce_quantity(update: Update,
                    context: CallbackContext) -> str:
    _, product_id = update.callback_query.data.split(':')
    current_quantity = int(update.callback_query.message.reply_markup['inline_keyboard'][0][1]['text'])
    if current_quantity > 1:
        context.bot.edit_message_reply_markup(
            chat_id=update.effective_chat.id,
            message_id=update.callback_query.message.message_id,
            reply_markup=make_prod_inline(quantity=(current_quantity - 1), product_id=product_id)
        )
    return 'HANDLE_DESCRIPTION'


def add_to_cart(redis: Redis,
                update: Update,
                context: CallbackContext) -> str:

    _, product_id = update.callback_query.data.split(':')
    quantity = int(update.callback_query.message.reply_markup['inline_keyboard'][0][1]['text'])
    
    elastic_token = get_or_create_elastic_token(redis)
    
    user_cart_id, is_empty = get_or_create_cart(redis, update.effective_chat.id, elastic_token)
    
    try:
        elastic_management.add_product_to_cart(elastic_token, product_id, user_cart_id, quantity)
    except requests.exceptions.HTTPError as error:
        if error.response.status_code == 400:
            product_stock = elastic_management.get_product_stock(elastic_token, product_id)
            available_pcs = product_stock['data']['available']
            quantity_in_cart = get_current_quantity_in_cart(redis, update.effective_chat.id, elastic_token, product_id)
            context.bot.send_message(
                update.effective_chat.id,
                dedent(
                    f'''
                    Sorry, you are trying to add too much pcs.

                    Now in your cart: {quantity_in_cart} pcs.
                    Available for order: {available_pcs} pcs.
                    '''
                )
            )
        else:
            context.bot.send_message(
                update.effective_chat.id,
                'Sorry, cant add this good to your cart.'
            )
    
    return 'HANDLE_DESCRIPTION'

def main_menu(update: Update,
              context: CallbackContext) -> str:
    elastic_token = get_or_create_elastic_token(redis)
    products = elastic_management.get_products(elastic_token)
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
    elastic_token = get_or_create_elastic_token(redis)
    product = elastic_management.get_product(elastic_token, product_id)
    product_stock = elastic_management.get_product_stock(elastic_token, product_id)

    response = requests.get(product['included']['main_images'][0]['link']['href'])
    context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=response.content,
        caption=dedent(
            f"""
            {product['data']['attributes']['name']}

            {product['data']['attributes']['description']}

            {product['data']['attributes']['price']['USD']['amount'] / 100} USD

            {product_stock['data']['available']} psc available
            """
        ),
        reply_markup=make_prod_inline(product_id=product_id)
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
                    CallbackQueryHandler(callback=main_menu, pattern='main_menu'),
                    CallbackQueryHandler(callback=partial(increase_quantity, redis), pattern='increase_quantity'),
                    CallbackQueryHandler(callback=reduce_quantity, pattern='reduce_quantity'),
                    CallbackQueryHandler(callback=partial(add_to_cart, redis), pattern='add_to_cart')
                ]
            },
            fallbacks=[]
        )
    )
    



    updater.start_polling()
    updater.idle()
