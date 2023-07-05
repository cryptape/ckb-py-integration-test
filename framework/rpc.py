import requests

import json


class RPCClient:
    def __init__(self, url):
        self.url = url

    def get_tip_block_number(self):
        return int(self.call("get_tip_block_number", []), 16)

    def get_current_epoch(self):
        return self.call("get_current_epoch", [])

    def local_node_info(self):
        return self.call("local_node_info", [])

    # //"QmUsZHPbjjzU627UZFt4k8j6ycEcNvXRnVGxCPKqwbAfQS",
    # "/ip4/192.168.2.100/tcp/8114"
    def add_node(self, peer_id, peer_address):
        return self.call("add_node", [peer_id, peer_address])

    def get_block_hash(self, block_number_hex):
        return self.call("get_block_hash", [block_number_hex])

    def get_block(self, block_hash, verbosity=None, with_cycles=None):
        return self.call("get_block", [block_hash, verbosity, with_cycles])

    def get_block_by_number(self, block_number, verbosity=None, with_cycles=None):
        """
        {
          "id": 42,
          "jsonrpc": "2.0",
          "method": "get_block_by_number",
          "params": [
            "0x0"
          ]
        }
        :return:
        """
        return self.call("get_block_by_number", [block_number, verbosity, with_cycles])

    def get_transaction_and_witness_proof(self, tx_hashes, block_hash=None):
        return self.call("get_transaction_and_witness_proof", [tx_hashes, block_hash])

    def truncate(self, block_hash):
        return self.call("truncate", [block_hash])

    def get_consensus(self):
        return self.call("get_consensus", [])

    def get_deployments_info(self):
        return self.call("get_deployments_info", [])

    def get_block_template(self, bytes_limit=None, proposals_limit=None, max_version=None):
        return self.call("get_block_template", [bytes_limit, proposals_limit, max_version])

    def tx_pool_info(self):
        return self.call("tx_pool_info", [])

    def get_tip_header(self):
        return self.call("get_tip_header", [])

    def get_transaction(self, tx_hash, verbosity=None, only_committed=None):
        return self.call("get_transaction", [tx_hash, verbosity, only_committed])

    def submit_block(self, work_id, block):
        return self.call("submit_block", [work_id, block])

    def call(self, method, params):
        headers = {'content-type': 'application/json'}
        data = {
            "id": 1,
            "jsonrpc": "2.0",
            "method": method,
            "params": params
        }
        print("request:url:{url},data:{data}".format(url=self.url, data=json.dumps(data)))
        response = requests.post(self.url, data=json.dumps(data), headers=headers).json()
        print("response:{response}".format(response=response))
        if 'error' in response.keys():
            error_message = response['error'].get('message', 'Unknown error')
            raise Exception(f"Error: {error_message}")

        return response.get('result', None)


if __name__ == '__main__':
    client = RPCClient("https://testnet.ckb.dev/")
    number = client.get_tip_block_number()
    print(number)
