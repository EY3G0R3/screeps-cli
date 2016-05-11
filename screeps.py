"""Screeps CLI

Usage:
  screeps.py log
  screeps.py download [--dest=<directory>] [--ptr] [--debug]
"""
import os
import logging

from docopt import docopt
import json
import requests
import websocket
import sys


def save(name, data, dest):
    with open('{}/{}.js'.format(dest, name), 'w') as f:
        f.write(data)


def download(email, password, arguments):
    print(arguments)
    dest = arguments.get('--dest')
    if not dest:
        dest = 'dist'

    if not os.path.isdir(dest):
        os.mkdir(dest)

    url = 'https://screeps.com/api/user/code'

    if arguments.get('--ptr'):
        url = 'https://screeps.com/ptr/api/user/code?branch=$activeWorld'

    auth = (email, password)
    response = requests.get(url, auth=auth)
    response.raise_for_status()
    data = response.json()

    if 'error' in data:
        sys.exit(data['error'])

    for module in data['modules']:
        if data['modules'][module]:
            if arguments.get('--debug'):
                print('save {}'.format(module))
            save(module, data['modules'][module], dest)
        else:
            try:
                os.remove('{}/{}.js'.format(dest, module))
            except OSError:
                pass


class ScreepsWSConnection(object):
    def __init__(self, email, password):
        self.email = email
        self.password = password

    def on_message(self, ws, message):
        if (message.startswith('auth ok')):
            ws.send('subscribe user:' + self.user_id + '/console')
            return

        if (message.startswith('time')):
            return

        data = json.loads(message)

        if 'messages' in data[1]:
            if 'log' in data[1]['messages']:
                for line in data[1]['messages']['log']:
                    print line
            return

        print('on_message', message)

    def on_error(self, ws, error):
        print(error)

    def on_close(self, ws):
        print("### closed ###")

    def on_open(self, ws):
        ws.send('auth {}'.format(self.token))

    def get_token(self):
        url = 'https://screeps.com/api/auth/signin'
        data = dict(email=self.email, password=self.password)
        response = requests.post(url=url, data=data)
        self.token = response.json()['token']

    def get_user_id(self):
        url = 'https://screeps.com/api/auth/me'
        headers = {'X-Token': self.token, 'X-Username': self.token}
        response = requests.get(url=url, headers=headers)
        self.user_id = response.json()['_id']

    def connect(self):
        url = 'wss://screeps.com/socket/websocket'
        ws = websocket.WebSocketApp(url=url,
                                    on_message=self.on_message,
                                    on_error=self.on_error,
                                    on_close=self.on_close,
                                    on_open=self.on_open)
        ws.run_forever(ping_interval=1)

    def start(self):
        self.get_token()
        self.get_user_id()
        self.connect()


def main():
    logging.basicConfig()
    arguments = docopt(__doc__)

    email = os.environ.get('email')
    password = os.environ.get('password')

    if not email or not password:
        sys.exit('Please set email and password as environment variables.')

    if arguments.get('log'):
        swsc = ScreepsWSConnection(email, password)
        swsc.start()

    if arguments.get('download'):
        download(email, password, arguments)


if __name__ == '__main__':
    main()
