from os import path
import requests
import pickle
from datetime import datetime
from django.conf import settings


CHANNEL_ID = '1653759302'
CHANNEL_SECRET = '123371074bdeed8827c67507778eb106'

def get_token():
    with open(path.join(settings.BASE_DIR, 'token.pickle'), 'rb') as f:
        try:
            token = pickle.load(f)
        except EOFError:
            raise
    # 有効なトークンがキャッシュされていればそれを返す
    if verify(token):
        return token
    # なければ再取得
    print('token is issued')
    headers = {
        'Content-Type': "application/x-www-form-urlencoded"
    }
    data = {
        'grant_type': "client_credentials",
        "client_id": CHANNEL_ID,
        'client_secret': CHANNEL_SECRET
    }
    res = requests.post(
        'https://api.line.me/v2/oauth/accessToken', data, headers=headers)
    token = res.json()['access_token']
    # 値をキャッシュ
    with open('data.pickle', 'wb') as f:
        pickle.dump(token, f)
    return token

def auth(func):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + get_token()
    }
    def wrapped_func(*args, **kwargs):
        return func(*args, **kwargs, headers=headers)
    return wrapped_func

def verify(token):
    if not token:
        return False

    VERIFY_URL = 'https://api.line.me/v2/oauth/verify'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    data = {
        'access_token': token
    }
    res = requests.post(VERIFY_URL, data, headers=headers)
    if 'error' in res.json():
        return False
    print('Token is OK')
    return True
