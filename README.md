# Telegram store
Telegram store based on [ElasticPath store management](https://euwest.cm.elasticpath.com/)

## How to install
For installing app you will need [redis server (6.0.16)](https://redis.io/docs/getting-started/installation/) and poetry (1.2.0)
```sh
git clone https://github.com/ilyashirko/telegram_store &&
cd telegram_store &&
python3 -m venv env &&
poetry install
```
You need .env file with:
```
TELEGRAM_BOT_TOKEN=
CLIENT_ID=

REDIS_HOST=
REDIS_PORT=
REDIS_PASSWORD=
REDIS_DB=
```
`TELEGRAM_BOT_TOKEN` [REQUIRED] you can get with [@BotFather](https://t.me/BotFather).  
`CLIENT_ID` [REQUIRED] you can get in the settings of [elasticpath](https://euwest.cm.elasticpath.com/)
`REDIS_HOST` [OPTIONAL] default = `localhost`  
`REDIS_PORT` [OPTIONAL] default = 6379  
`REDIS_PASSWORD` [OPTIONAL] default = None  
`REDIS_DB` [OPTIONAL] default = 0  
[read more about redis settings](https://developer.redis.com/develop/python/)  

Also you need `privacy_policy.pdf` file in root folder. This is for taking personal info according to law.  

## Run bot
```sh
python3 telegram_bot.py
```
## Demo version
[click here](https://t.me/ilyashirko_store_demo_bot)