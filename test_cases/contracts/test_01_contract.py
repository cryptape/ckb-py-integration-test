import json
import os
import time

import pytest

from framework.config import MINER_PRIVATE_1
from framework.helper.ckb_cli import estimate_cycles
from framework.helper.contract import deploy_ckb_contract, invoke_ckb_contract
from framework.helper.miner import miner_until_tx_committed, make_tip_height_number, miner_with_version
from framework.test_node import CkbNodeConfigPath, CkbNode
from framework.util import get_project_root


def get_all_files(directory):
    file_list = []
    for root, directories, files in os.walk(directory):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            file_list.append(file_path)
    return file_list


def get_successful_files():
    files = get_all_files(f"{get_project_root()}/source/contract/test_cases")
    files_list = ["spawn_exceeded_max_content_length",
                  "loop_contract",
                  "spawn_exec_memory_limit_le_7",
                  "spawn_argc_not_eq",
                  "spawn_argc_is_u64_max"
                  ]
    return [s for s in files if not any(s.endswith(suffix) for suffix in files_list)]


def get_failed_files():
    project_root = get_project_root()
    files = get_all_files(f"{get_project_root()}/source/contract/test_cases")

    files_list = ["spawn_exceeded_max_content_length",
                  "loop_contract",
                  "spawn_exec_memory_limit_le_7",
                  "spawn_argc_not_eq",
                  "spawn_argc_is_u64_max"
                  ]
    # return [s for s in files if not any(s.endswith(suffix) for suffix in files_list)]
    return [f"{project_root}/source/contract/test_cases/{x}" for x in files_list]


class TestHelperContract:
    success_files = get_successful_files()
    failed_files = get_failed_files()

    @classmethod
    def setup_class(cls):
        cls.node = CkbNode.init_dev_by_port(CkbNodeConfigPath.CURRENT_TEST, "contract/node", 8114, 8115)
        cls.node.prepare()
        cls.node.start()
        make_tip_height_number(cls.node, 2000)
        pass
        # dep   loy `anyone_can_pay` contract

    @classmethod
    def teardown_class(cls):
        cls.node.stop()
        cls.node.clean()

    @pytest.mark.parametrize("path", success_files)
    # @pytest.mark.skip
    def test_deploy_and_invoke_demo(self, path):
        return deploy_and_invoke(MINER_PRIVATE_1, path, self.node)

    @pytest.mark.parametrize("path", failed_files)
    def test_deploy_and_invoke_demo_failed(self, path):
        try:
            deploy_and_invoke(MINER_PRIVATE_1, path, self.node)
        except Exception as e:
            print(e)

    @pytest.mark.skip
    def test_stack_overflow(self):
        """
        contract link:
        https://github.com/gpBlockchain/ckb-test-contracts/blob/main/rust/acceptance-contracts/contracts/spawn_demo/src/spawn_recursive.rs
        :return:
        """
        deploy_and_invoke(MINER_PRIVATE_1,
                          f"{get_project_root()}/source/contract/test_cases/spawn_recursive",
                          self.node)

    @pytest.mark.skip
    def test_estimate_cycles_bug(self):
        """
        https://github.com/gpBlockchain/ckb-test-contracts/blob/main/rust/acceptance-contracts/contracts/spawn_demo/src/spawn_times.rs
        send_transaction( big cycle tx )
            return tx;
        query tx status
            return tx_status == rejected
        if status == pending ,is  bug
        query estimate_cycles
            return : ExceededMaximumCycles
            if return cycles > 1045122714,is bug
        :return:
        """
        deploy_hash = deploy_ckb_contract(MINER_PRIVATE_1,
                                          "/Users/guopenglin/WebstormProjects/gp1/ckb-test-contracts/rust/acceptance-contracts/build/release/spawn_times",
                                          enable_type_id=True,
                                          api_url=self.node.getClient().url)
        miner_until_tx_committed(self.node, deploy_hash)
        for i in range(1, 10):
            invoke_hash = invoke_ckb_contract(account_private=MINER_PRIVATE_1,
                                              contract_out_point_tx_hash=deploy_hash,
                                              contract_out_point_tx_index=0,
                                              type_script_arg="0x02", data=f"0x{i:02x}",
                                              hash_type="type",
                                              api_url=self.node.getClient().url)
            time.sleep(5)
            transaction = self.node.getClient().get_transaction(invoke_hash)
            # if transaction["tx_status"]['status'] == ""
            if transaction["tx_status"]['status'] == "rejected":
                continue
            if transaction["tx_status"]['status'] == "pending":
                # bug
                # es cycle
                del transaction['transaction']['hash']
                with open("/tmp/tmp.json", 'w') as tmp_file:
                    tmp_file.write(json.dumps(transaction['transaction']))
                for i in range(5):
                    try:
                        result = estimate_cycles("/tmp/tmp.json",
                                                 api_url=self.node.getClient().url)
                        print(f"estimate_cycles:{result}")
                    except Exception:
                        pass


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

    return invoke_hash
