from framework.config import SPAWN_CONTRACT_PATH
from framework.helper.contract import deploy_ckb_contract, CkbContract
from framework.helper.miner import miner_until_tx_committed
from framework.test_node import CkbNode


class SpawnContract(CkbContract):

    def __init__(self, contract_hash=None, contract_tx_index=None):
        self.contract_hash = contract_hash
        self.contract_tx_index = contract_tx_index
        if contract_hash is None:
            self.deployed = False
        self.contract_path = SPAWN_CONTRACT_PATH
        self.method = {
            "demo": {"args": "0x", "data": "0x"}
        }

    def deploy(self, account_private, node: CkbNode):
        if self.deployed:
            return
        self.contract_path = deploy_ckb_contract(account_private, self.contract_path, api_url=node.getClient().url)
        self.contract_tx_index = 0
        miner_until_tx_committed(node, self.contract_path)
        self.deployed = True

    def get_deploy_hash_and_index(self) -> (str, int):
        if not self.deployed:
            raise Exception("pls deploy first")
        return self.contract_path, self.contract_tx_index

    def get_arg_and_data(self, key) -> (str, str):
        if key not in self.method.keys():
            # return "0x0","0x0"
            raise Exception("key not exist in method list")
        return self.method[key]["args"], self.method[key]["data"]
