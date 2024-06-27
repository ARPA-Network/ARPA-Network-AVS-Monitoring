#!/usr/bin/env python

import platform
import os
import yaml
from time import sleep
from eth_account import Account
from web3 import Web3
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from prometheus_client import start_http_server, Counter, REGISTRY, Info


class HTTPRequestHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type','text/html')
            self.end_headers()
            self.wfile.write(bytes("<b> Hello World !</b>", "utf-8"))
            request_counter.labels(status_code='200', instance=platform.node()).inc()
        else:
            self.send_error(404)
            request_counter.labels(status_code='404', instance=platform.node()).inc()


def get_address_from_keystore(keystore_path, password):
    with open(keystore_path) as keyfile:
        encrypted_key = keyfile.read()
        keystore_json = json.loads(encrypted_key)
    
    private_key = Account.decrypt(keystore_json, password)
    
    account = Account.from_key(private_key)
    
    return account.address


def get_address():
    config_path = 'config.yml'
    keystore_path = 'node.keystore'
    password = ''
    private_key = ''
    if os.path.exists(config_path):
        with open(config_path, 'r') as file:
            data = yaml.safe_load(file)
            if 'account' in data and 'private_key' in data['account']:
                private_key = data['account']['private_key']
            elif 'account' in data and 'keystore' in data['account'] and 'password' in data['account']['keystore']:
                password = data['account']['keystore']['password']
    
    # Keystore takes higher priority
    if os.path.exists(keystore_path) and password != '':
        return get_address_from_keystore(keystore_path, password)
    
    return Account.from_key(private_key)
    
                
if __name__ == '__main__':
    address = get_address()
    print('address:' + address)
    start_http_server(9000)
    request_counter = Counter('http_requests', 'HTTP request', ["status_code", "instance"])
    address_info = Info('node_address', 'Node address of current node client')
    address_info.info({'node_address': address})
    webServer = HTTPServer(("localhost", 8080), HTTPRequestHandler).serve_forever()
    print("Server started")