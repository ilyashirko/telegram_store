import requests
import json
from datetime import datetime

# STORE_ID = '46b51b1e-1b86-41db-87bc-58298ac07645'

# SECRET_KEY = 'RAqsLCdNDG9yLb18TsScXiEY3LiRoevV0nr1IQ8qF0'

# URL = 'https://api.moltin.com/v2/carts/abc'
# CATALOG_URL = 'https://api.moltin.com/catalog'
# PRODUCTS_URL = 'https://api.moltin.com/catalog/products'
# NODES_URL = 'https://api.moltin.com/catalog/nodes'
# BASE_URL = 'https://api.moltin.com'


def get_token(client_id: str) -> str:
    access_token_url = 'https://api.moltin.com/oauth/access_token'
    access_token_data = {
        'client_id': client_id,
        'grant_type': 'implicit',
    }
    response = requests.get(access_token_url, data=access_token_data)
    response.raise_for_status()
    token_meta = response.json()
    print(token_meta['access_token'])
    print(type(token_meta['access_token']))
    return token_meta['access_token'], token_meta['expires']


def get_product(token: str, product_id: str) -> dict:
    headers = {
        "Authorization": f"Bearer {token}"
    }
    params = {
        "include": "main_image,manage_stock",
    }
    product_url = f'https://api.moltin.com/catalog/products/{product_id}'
    response = requests.get(product_url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

def get_product_stock(token: str, product_id: str) -> dict:
    headers = {
        "Authorization": f"Bearer {token}"
    }
    url = f'https://api.moltin.com/v2/inventories/{product_id}'
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    print(json.dumps(response.json(), indent=6))
    return response.json()


def get_product_main_photo(token, product_id):
    headers = {
        "Authorization": f"Bearer {token}"
    }
    main_photo_url = f'https://api.moltin.com/pcm/products/{product_id}/relationships/files'
    print(main_photo_url)
    response = requests.get(main_photo_url, headers=headers)
    response.raise_for_status()
    return response.content

def get_products(token: str) -> dict:
    headers = {
        "Authorization": f"Bearer {token}",
        "EP-Channel": "web store"
    }
    products_url = 'https://api.moltin.com/catalog/nodes/c508ef18-c1e1-421b-a423-9cd4ddaf18da/relationships/products'
    response = requests.get(products_url, headers=headers)
    response.raise_for_status()
    return response.json()


def create_customer(token: str,
                    name: str = 'ilyashirko',
                    email: str = 'ilyashirko@gmail.com',
                    password: str = 'password') -> dict:
    url = 'https://api.moltin.com/v2/customers'
    headers = {
        "Authorization": f"Bearer {token}",
    }
    json_data = {
        "data": {
            "type": "customer",
            "name": name,
            "email": email,
            "password": password,
        }
    }
    response = requests.post(url, headers=headers, json=json_data)
    response.raise_for_status()
    return response.json()


def get_customer_token(token: str,
                       email: str = 'ilyashirko@gmail.com',
                       password: str = 'password') -> str:
    url = 'https://api.moltin.com/v2/customers/tokens'
    headers = {
        "Authorization": f"Bearer {token}",
        'Content-Type': 'application/json',
    }
    json_data = {
        "data": {
            "type": "token",
            "email": email,
            "password": password,
            "authentication_mechanism": "password"
        }
    }
    response = requests.post(url, headers=headers, json=json_data)
    response.raise_for_status()
    
    return response.json()['data']['token']

def get_cart(token: str,
             cart_id: str) -> dict:
    url = f'https://api.moltin.com/v2/carts/{cart_id}'
    headers = {
        "Authorization": f"Bearer {token}"
    }
    params = {
        "include": "items",
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()


def convert_api_date_to_timestamp(source_date):
    datetime_obj = datetime.fromisoformat(source_date + '+03:00')
    return int(datetime_obj.timestamp())

def create_cart(token: str,
                name: str = 'new_cart') -> tuple:
    url = 'https://api.moltin.com/v2/carts'
    headers = {
        "Authorization": f"Bearer {token}",
        'Content-Type': 'application/json',
    }
    json_data = {
        "data": {
            "name": name,
        }
    }
    response = requests.post(url, headers=headers, json=json_data)
    response.raise_for_status()
    cart_summary = response.json()['data']
    expired_at = cart_summary['meta']['timestamps']['expires_at']
    return cart_summary['id'], convert_api_date_to_timestamp(expired_at)




def add_product_to_cart(token: str,
                        prod_id: str,
                        cart_id: str,
                        quantity: int):
    url = f'https://api.moltin.com/v2/carts/{cart_id}/items'
    headers = {
        "Authorization": f"Bearer {token}",
        'Content-Type': 'application/json',
    }
    json_data = {
        "data": {
            "id": prod_id,
            "type": 'cart_item',
            'quantity': quantity
        }
    }
    response = requests.post(url, headers=headers, json=json_data)
    
    response.raise_for_status()
    return response.json()

def remove_product_from_cart(token: str, cart_id: str, item_id: str) -> dict:
    url = f'https://api.moltin.com/v2/carts/{cart_id}/items/{item_id}'
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.delete(url, headers=headers)
    response.raise_for_status()
    return response.json()

if __name__ == '__main__':
    CLIENT_ID = 'R25Ym1Xy9u0xBXdqGxFAmnSjgF3a5R7qLI0Vaoijrr'

    CUSTOMER_ID = '6422150a-beda-4ed4-9f0b-d5790dcfd293'

    TELEGRAM_ID = '434137786'

    CART_ID = 'fa5ce5be-62ea-4f72-8550-20ce6587b603'


    token = get_token(CLIENT_ID)
    #token = 'fa5ce5be-62ea-4f72-8550-20ce6587b603'
    # print(json.dumps(token, indent=2))

    # input(json.dumps(create_cart(token, '23234234'), indent=2))
    input(create_cart(token, 'blabla'))
    try:
        products = get_products(token)
    except requests.exceptions.HTTPError as error:
        input(error.response.status_code)
    CART_ID = create_cart(token, 'blabla')
    prod_id = products['data'][1]['id']
    add_product_to_cart(token, prod_id, CART_ID, 5)
    input(json.dumps(get_cart(token, CART_ID), indent=2))


    input()
    try:
        customer_token = get_customer_token(token)
    except requests.exceptions.HTTPError:
        create_customer(token)
        customer_token = get_customer_token(token)

    add_prod_report = add_product_to_cart(token, customer_token, first_product['id'], 'some reference', CART_ID)
    print(json.dumps(add_prod_report, indent=2))
    # print(create_cart(token, customer_token))