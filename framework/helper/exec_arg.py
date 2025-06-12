from framework.config import EXEC_ARG_PATH
from framework.helper.contract import deploy_ckb_contract, CkbContract
from framework.helper.miner import miner_until_tx_committed
from framework.helper.ckb_cli import util_key_info_by_private_key
from framework.helper.contract import invoke_ckb_contract

from framework.test_node import CkbNode
from framework.util import (
    ckb_hash_script,
    to_big_uint128_le_compatible,
    to_int_from_big_uint128_le,
)
from framework.helper.contract import get_ckb_contract_codehash


class ExecArgContract(CkbContract):

    def __init__(self, contract_hash=None, contract_tx_index=None):
        self.contract_hash = contract_hash
        self.contract_tx_index = contract_tx_index
        if contract_hash is None:
            self.deployed = False
        else:
            self.deployed = True
        self.contract_path = EXEC_ARG_PATH
        self.method = {"demo": {"args": "0x", "data": "0x"}}

    def deploy(self, account_private, node: CkbNode):
        if self.deployed:
            return
        self.contract_hash = deploy_ckb_contract(
            account_private, self.contract_path, api_url=node.getClient().url
        )
        self.contract_tx_index = 0
        miner_until_tx_committed(node, self.contract_hash)
        self.deployed = True

    def get_deploy_hash_and_index(self) -> (str, int):
        if not self.deployed:
            raise Exception("pls deploy first")
        return self.contract_hash, self.contract_tx_index

    def get_code_hash(self, type_id, api):
        return get_ckb_contract_codehash(
            self.contract_hash, self.contract_tx_index, type_id, api
        )

    def get_owner_arg_by_lock_arg(self, lock_arg):
        return ckb_hash_script(lock_arg)

    @classmethod
    def get_test_data(cls, mb_size, kb_size, byte_size) -> (str, str):
        return "0x1234", to_big_uint128_le_compatible(
            mb_size * 100000000 + kb_size * 10000 + byte_size
        )

    def get_arg_and_data(self, key) -> (str, str):
        if key not in self.method.keys():
            # return "0x0","0x0"
            raise Exception("key not exist in method list")
        return self.method[key]["args"], self.method[key]["data"]
