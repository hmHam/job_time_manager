import requests
from job_time.auth import auth
import json
from pprint import pprint
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument('--make', nargs='?', const=True, default=False)
parser.add_argument('--gets', nargs='?', const=True, default=False)
parser.add_argument('--register', default=False)
parser.add_argument('--delete', default=False)
parser.add_argument('--image', '-i', nargs=3, default=False)


@auth
def make_rich(headers={}):
    URL = 'https://api.line.me/v2/bot/richmenu'
    with open('menu.json', 'r') as f:
        data = json.load(f)
    return requests.post(URL, json=data, headers=headers)

@auth
def get_richs(headers={}):
    URL = 'https://api.line.me/v2/bot/richmenu/list'
    return requests.get(URL, headers=headers)

@auth
def register_rich(menu_id, headers={}):
    URL = 'https://api.line.me/v2/bot/user/all/richmenu/{richMenuId}'.format(richMenuId=menu_id)
    return requests.post(URL, json={}, headers=headers)

@auth
def delete_rich(menu_id, headers={}):
    URL = 'https://api.line.me/v2/bot/richmenu/{richMenuId}'.format(richMenuId=menu_id)
    return requests.delete(URL, headers=headers)

@auth
def upload_rich(menu_id, content_type, image_path, headers={}):
    URL = 'https://api-data.line.me/v2/bot/richmenu/{richMenuId}/content'.format(richMenuId=menu_id)
    headers['content-type'] = content_type
    return requests.post(URL, data=open(image_path, 'rb'), headers=headers)


if __name__ == '__main__':
    args = parser.parse_args()
    if args.make:
        pprint(make_rich().json())
    if args.gets:
        res = get_richs().json()
        menus = res['richmenus']
        print('count', len(menus))
        pprint(menus)
    if args.register:
        pprint(register_rich(args.register).json())
    if args.delete:
        pprint(delete_rich(args.delete).json())
    if args.image:
        pprint(upload_rich(*args.image).text)