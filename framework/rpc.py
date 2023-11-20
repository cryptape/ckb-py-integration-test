import time

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

    def get_fee_rate_statics(self, target=None):
        return self.call("get_fee_rate_statics", [target])

    def generate_epochs(self, epoch):
        return self.call("generate_epochs", [epoch])

    def generate_block(self):
        return self.call("generate_block",[])

    def get_deployments_info(self):
        return self.call("get_deployments_info", [])

    def get_block_template(self, bytes_limit=None, proposals_limit=None, max_version=None):
        return self.call("get_block_template", [bytes_limit, proposals_limit, max_version])

    def tx_pool_info(self):
        return self.call("tx_pool_info", [])

    def get_tip_header(self):
        return self.call("get_tip_header", [])

    def get_transaction(self, tx_hash, verbosity=None, only_committed=None):
        if verbosity is None and only_committed is None:
            return self.call("get_transaction", [tx_hash])
        return self.call("get_transaction", [tx_hash, verbosity, only_committed])

    def send_transaction(self, tx, outputs_validator="passthrough"):
        return self.call("send_transaction", [tx, outputs_validator])

    def get_raw_tx_pool(self, verbose=None):
        return self.call("get_raw_tx_pool", [verbose])

    def clear_tx_pool(self):
        return self.call("clear_tx_pool", [])

    def get_peers(self):
        return self.call("get_peers", [])

    def set_network_active(self, state):
        return self.call("set_network_active", [state])

    def remove_transaction(self, tx_hash):
        return self.call("remove_transaction", [tx_hash])

    def get_live_cell(self, index, tx_hash, with_data=True):
        return self.call("get_live_cell", [{"index": index, "tx_hash": tx_hash}, with_data])

    def submit_block(self, work_id, block):
        return self.call("submit_block", [work_id, block])

    def get_cells_capacity(self, script):
        return self.call("get_cells_capacity", [script])

    def call(self, method, params):

        headers = {'content-type': 'application/json'}
        data = {
            "id": 42,
            "jsonrpc": "2.0",
            "method": method,
            "params": params
        }
        print(f"request:url:{self.url},data:\n{json.dumps(data)}")
        for i in range(15):
            try:
                response = requests.post(self.url, data=json.dumps(data), headers=headers).json()
                print(f"response:\n{json.dumps(response)}")
                if 'error' in response.keys():
                    error_message = response['error'].get('message', 'Unknown error')
                    raise Exception(f"Error: {error_message}")

                return response.get('result', None)
            except requests.exceptions.ConnectionError as e:
                print(e)
                print("request too quickly, wait 2s")
                time.sleep(2)
                continue
            except Exception as e:
                print("Exception:", e)
                raise e
        raise Exception("request time out")


if __name__ == '__main__':
    client = RPCClient("https://testnet.ckb.dev/")
    number = client.get_tip_block_number()
    print(number)
