import os

import pytest

from framework.config import MINER_PRIVATE_1
from framework.helper.contract import deploy_ckb_contract, invoke_ckb_contract
from framework.helper.miner import miner_until_tx_committed, make_tip_height_number
from framework.test_node import CkbNodeConfigPath, CkbNode
from framework.util import get_project_root


def get_all_files(directory):
    file_list = []
    for root, directories, files in os.walk(directory):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            file_list.append(file_path)
    return file_list


class TestHelperContract:
    files = get_all_files(f"{get_project_root()}/source/contract/test_cases")

    @classmethod
    def setup_class(cls):
        cls.node = CkbNode.init_dev_by_port(CkbNodeConfigPath.CURRENT_TEST, "contract/node", 8114, 8115)
        cls.node.prepare()
        cls.node.start()

        make_tip_height_number(cls.node, 2000)
        # dep   loy `anyone_can_pay` contract

    @classmethod
    def teardown_class(cls):
        cls.node.stop()
        cls.node.clean()

    @pytest.mark.parametrize("path", files)
    @pytest.mark.skip
    def test_deploy_and_invoke_demo(self, path):
        deploy_and_invoke(MINER_PRIVATE_1, path, self.node)

    def test_stack_overflow(self):
        """
        contract link:
        https://github.com/gpBlockchain/ckb-test-contracts/blob/main/rust/acceptance-contracts/contracts/spawn_demo/src/spawn_out_of_memory.rs

        :return:
        """
        deploy_and_invoke(MINER_PRIVATE_1,
                          f"{get_project_root()}/source/contract/test_cases/spawn_out_of_memory",
                          self.node)

    def test_stack_overflow_2(self):
        """
        contract link:
        https://github.com/gpBlockchain/ckb-test-contracts/blob/main/rust/acceptance-contracts/contracts/spawn_demo/src/spawn_recursive.rs
        :return:
        """
        deploy_and_invoke(MINER_PRIVATE_1,
                          f"{get_project_root()}/source/contract/test_cases/spawn_recursive",
                          self.node)


def deploy_and_invoke(account, path, node):
    deploy_hash = deploy_ckb_contract(account,
                                      path,
                                      enable_type_id=True,
                                      api_url=node.getClient().url)
    miner_until_tx_committed(node, deploy_hash)
    invoke_hash = invoke_ckb_contract(account_private=account,
                                      contract_out_point_tx_hash=deploy_hash,
                                      contract_out_point_tx_index=0,
                                      type_script_arg="0x02", data="0x1234",
                                      hash_type="type",
                                      api_url=node.getClient().url)
    miner_until_tx_committed(node, invoke_hash)
