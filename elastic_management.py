import requests
import json
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
    return response.json()['access_token']


def get_product(token: str, product_id: str) -> dict:
    headers = {
        "Authorization": f"Bearer {token}"
    }
    params = {
        "include": "main_image"
    }
    product_url = f'https://api.moltin.com/catalog/products/{product_id}'
    response = requests.get(product_url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

def get_product_main_photo(token, product_id):
    headers = {
        "Authorization": f"Bearer {token}"
    }
    main_photo_url = f'https://api.moltin.com/pcm/products/{product_id}/relationships/files'
    print(main_photo_url)
    response = requests.get(main_photo_url, headers=headers)
    response.raise_for_status()
    input(type(response.content))
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


def create_cart(token: str,
                customer_token: str,
                name: str = 'new_cart',
                description: str = 'description of new cart') -> str:
    url = 'https://api.moltin.com/v2/carts'
    headers = {
        "Authorization": f"Bearer {token}",
        'Content-Type': 'application/json',
        "x-moltin-customer-token": customer_token
    }
    json_data = {
        "data": {
            "name": name,
            "description": description,
        }
    }
    response = requests.post(url, headers=headers, json=json_data)
    response.raise_for_status()
    return response.json()['data']['id']




def add_product_to_cart(token: str,
                        customer_token: str,
                        prod_id: str,
                        reference: str,
                        cart_id: str):
    url = f'https://api.moltin.com/v2/carts/{cart_id}/items'
    headers = {
        "Authorization": f"Bearer {token}",
        'Content-Type': 'application/json',
    }
    json_data = {
        "data": {
            "id": prod_id,
            "type": 'cart_item',
            'quantity': 1
        }
    }
    response = requests.post(url, headers=headers, json=json_data)
    response.raise_for_status()
    return response.json()



if __name__ == '__main__':
    CLIENT_ID = 'R25Ym1Xy9u0xBXdqGxFAmnSjgF3a5R7qLI0Vaoijrr'

    CUSTOMER_ID = '6422150a-beda-4ed4-9f0b-d5790dcfd293'

    TELEGRAM_ID = '434137786'

    CART_ID = 'fa5ce5be-62ea-4f72-8550-20ce6587b603'


    token = get_token(CLIENT_ID)
    print(token)

    products = get_products(token)

    prod_id = products['data'][1]['id']

    input(get_product_main_photo(token, prod_id))


    input()
    try:
        customer_token = get_customer_token(token)
    except requests.exceptions.HTTPError:
        create_customer(token)
        customer_token = get_customer_token(token)

    add_prod_report = add_product_to_cart(token, customer_token, first_product['id'], 'some reference', CART_ID)
    print(json.dumps(add_prod_report, indent=2))
    # print(create_cart(token, customer_token))