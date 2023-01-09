import requests

from datetime import datetime


def get_token(client_id: str) -> str:
    access_token_url = 'https://api.moltin.com/oauth/access_token'
    access_token_data = {
        'client_id': client_id,
        'grant_type': 'implicit',
    }
    response = requests.get(access_token_url, data=access_token_data)
    response.raise_for_status()
    token_meta = response.json()
    return token_meta['access_token'], token_meta['expires']


def get_product(token: str, product_id: str) -> dict:
    product_url = f'https://api.moltin.com/catalog/products/{product_id}'
    headers = {
        "Authorization": f"Bearer {token}"
    }
    params = {
        "include": "main_image",
    }
    response = requests.get(product_url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()


def get_product_stock(token: str, product_id: str) -> dict:
    url = f'https://api.moltin.com/v2/inventories/{product_id}'
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


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
                    email: str = 'ilyashirko@gmail.com') -> dict:
    url = 'https://api.moltin.com/v2/customers'
    headers = {
        "Authorization": f"Bearer {token}",
    }
    post_data = {
        "data": {
            "type": "customer",
            "name": name,
            "email": email,
        }
    }
    response = requests.post(url, headers=headers, json=post_data)
    response.raise_for_status()
    return response.json()


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


def create_cart(token: str,
                name: str = 'new_cart') -> tuple:
    url = 'https://api.moltin.com/v2/carts'
    headers = {
        "Authorization": f"Bearer {token}",
        'Content-Type': 'application/json',
    }
    post_data = {
        "data": {
            "name": name,
        }
    }
    response = requests.post(url, headers=headers, json=post_data)
    response.raise_for_status()
    cart_summary = response.json()['data']

    expired_at = cart_summary['meta']['timestamps']['expires_at']
    datetime_obj = datetime.fromisoformat(expired_at + '+03:00')

    return cart_summary['id'], int(datetime_obj.timestamp())


def add_product_to_cart(token: str,
                        prod_id: str,
                        cart_id: str,
                        quantity: int):
    url = f'https://api.moltin.com/v2/carts/{cart_id}/items'
    headers = {
        "Authorization": f"Bearer {token}",
        'Content-Type': 'application/json',
    }
    post_data = {
        "data": {
            "id": prod_id,
            "type": 'cart_item',
            'quantity': quantity
        }
    }
    response = requests.post(url, headers=headers, json=post_data)
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
