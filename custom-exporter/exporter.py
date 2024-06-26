#!/usr/bin/env python

import platform
from time import sleep
from eth_account import Account
from web3 import Web3
from http.server import BaseHTTPRequestHandler, HTTPServer
from prometheus_client import start_http_server, Counter, REGISTRY, Enum

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

def get_address(private_key):
    account = Account.from_key(private_key)
    return account.address
    
                
if __name__ == '__main__':
    # print(get_address(''))
    start_http_server(9000)
    request_counter = Counter('http_requests', 'HTTP request', ["status_code", "instance"])

    webServer = HTTPServer(("localhost", 8080), HTTPRequestHandler).serve_forever()
    print("Server started")