import time

import requests

import json


class CKBLightRPCClient:

    def __init__(self, url):
        self.url = url

    def set_scripts(self, script_status, command="all"):
        return self.call("set_scripts", [script_status, command])

    def get_scripts(self):
        return self.call("get_scripts", [])

    def get_cells_capacity(self, script):
        return self.call("get_cells_capacity", [script])

    def get_cells(self, search_key, order, limit, after):
        return self.call2("get_cells", [search_key, order, limit, after])

    def fetch_transaction(self, tx_hash):
        return self.call("fetch_transaction", [tx_hash])

    def get_transactions(self, search_key, order, limit, after):
        return self.call("get_transactions", [search_key, order, limit, after])

    def send_transaction(self,tx):
        return self.call("send_transaction",[tx])

    def fetch_transaction(self,tx_hash):
        return self.call("fetch_transaction",[tx_hash])

    def call(self, method, params):

        headers = {'content-type': 'application/json'}
        data = {
            "id": 42,
            "jsonrpc": "2.0",
            "method": method,
            "params": params
        }
        print("request:url:{url},data:\n{data}".format(url=self.url, data=json.dumps(data)))
        for i in range(100):
            try:
                response = requests.post(self.url, data=json.dumps(data), headers=headers).json()
                print("response:\n{response}".format(response=json.dumps(response)))
                if 'error' in response.keys():
                    error_message = response['error'].get('message', 'Unknown error')
                    raise Exception(f"Error: {error_message}")

                return response.get('result', None)
            except requests.exceptions.ConnectionError as e:
                print(e)
                print("request too quickly, wait 2s")
                time.sleep(2)
                continue
        raise Exception("request time out")

    def call2(self, method, params):

        headers = {'content-type': 'application/json'}
        data = {
            "id": 42,
            "jsonrpc": "2.0",
            "method": method,
            "params": params
        }
        print("request:url:{url},data:\n{data}".format(url=self.url, data=json.dumps(data)))
        for i in range(100):
            try:
                response = requests.post(self.url, data=json.dumps(data), headers=headers).json()
                # print("response:\n{response}".format(response=json.dumps(response)))
                if 'error' in response.keys():
                    error_message = response['error'].get('message', 'Unknown error')
                    raise Exception(f"Error: {error_message}")

                return response.get('result', None)
            except requests.exceptions.ConnectionError as e:
                print(e)
                print("request too quickly, wait 2s")
                time.sleep(2)
                continue
        raise Exception("request time out")
