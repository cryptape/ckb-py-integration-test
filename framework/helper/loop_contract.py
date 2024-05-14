from framework.config import LOOP_CONTRACT_PATH
from framework.helper.contract import deploy_ckb_contract, CkbContract
from framework.helper.miner import miner_until_tx_committed
from framework.test_node import CkbNode


class LoopContract(CkbContract):

    def __init__(self, contract_hash=None, contract_tx_index=None):
        self.contract_hash = contract_hash
        self.contract_tx_index = contract_tx_index
        if contract_hash is None:
            self.deployed = False
        self.contract_path = LOOP_CONTRACT_PATH
        self.method = {
            "cpu_5000w_cycle": {"args": "0x02", "data": "0x46c32300000000000000000000000000"},
            "cpu_1yi_cycle":{"args":"0x02","data":"0x8c864700000000000000000000000000"},
            "cpu_2yi_cycle": {"args": "0x02", "data": "0x180d8f00000000000000000000000000"},
            "cpu_4yi_cycle": {"args": "0x02", "data": "0x301a1e01000000000000000000000000"},
            "cpu_8yi_cycle": {"args": "0x02", "data": "0x60343c02000000000000000000000000"},
            "cpu_16yi_cycle": {"args": "0x02", "data": "0xc0687804000000000000000000000000"}
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
