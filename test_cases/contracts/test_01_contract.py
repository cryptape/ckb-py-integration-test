import os
import time

from parameterized import parameterized

from framework.basic import CkbTest
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
    files_list = [
        "spawn_cycle_inc_when_contains_recursion_and_loop_spawn",
        "spawn_source_is_input_cell",
        "spawn_loop_times",
        "spawn_source_is_output_cell",
        "spawn_recursion_times",
        "ckb_pipe",
        "spawn_argc_is_large",
        "spawn_place_is_witness",
        "loop_contract",
        "exec_with_block_opcode",
        "rfc49_atomic",
    ]
    return [s for s in files if not any(s.endswith(suffix) for suffix in files_list)]


def get_failed_files():
    project_root = get_project_root()
    files = get_all_files(f"{get_project_root()}/source/contract/test_cases")

    files_list = [
        "spawn_cycle_inc_when_contains_recursion_and_loop_spawn",
        "spawn_source_is_input_cell",
        "spawn_loop_times",
        "spawn_source_is_output_cell",
        "spawn_recursion_times",
        "ckb_pipe",
        "spawn_argc_is_large",
        "spawn_place_is_witness",
        "loop_contract",
        "exec_with_block_opcode",
        "rfc49_atomic",
    ]
    # return [s for s in files if not any(s.endswith(suffix) for suffix in files_list)]
    return [f"{project_root}/source/contract/test_cases/{x}" for x in files_list]


class TestHelperContract(CkbTest):
    success_files = get_successful_files()
    failed_files = get_failed_files()

    @classmethod
    def setup_class(cls):
        cls.node = cls.CkbNode.init_dev_by_port(
            cls.CkbNodeConfigPath.CURRENT_TEST, "contract/node", 8114, 8115
        )
        cls.node.prepare()
        cls.node.start()
        cls.Miner.make_tip_height_number(cls.node, 2000)
        cls.node1 = cls.CkbNode.init_dev_by_port(
            cls.CkbNodeConfigPath.v200, "contract/node1", 8116, 8117
        )
        cls.node1.prepare()
        cls.node1.start()
        cls.node1.connected(cls.node)
        cls.Node.wait_node_height(cls.node1, 2000, 200)

    @classmethod
    def teardown_class(cls):
        cls.node.stop()
        cls.node.clean()
        cls.node1.stop()
        cls.node1.clean()

    @parameterized.expand(success_files)
    # @pytest.mark.skip
    def test_01_deploy_and_invoke_demo(self, path):
        """
        1. Retrieve the paths of successful files from `project_root/source/contract/test_cases` by excluding the files specified in `files_list`.
        2. deploy and invoke contract
        """
        self.deploy_and_invoke(self.Config.MINER_PRIVATE_1, path, self.node)
        tip_number = self.node.getClient().get_tip_block_number()
        self.Node.wait_node_height(self.node1, tip_number, 200)

    @parameterized.expand(failed_files)
    def test_02_deploy_and_invoke_demo_failed(self, path):
        """
        1. Retrieve the paths of failed files from `project_root/source/contract/test_cases` by including only the files specified in `files_list`.
        2. deploy and invoke contract
        Note: If no exception is thrown, the test will fail.
        """
        try:
            self.deploy_and_invoke(self.Config.MINER_PRIVATE_1, path, self.node)
            self.fail("Did not raise an exception as expected!")
        except Exception as e:
            print(e)
        tip_number = self.node.getClient().get_tip_block_number()
        self.Node.wait_node_height(self.node1, tip_number, 200)

    def deploy_and_invoke(self, account, path, node, try_count=5):
        if try_count < 0:
            raise Exception("try out of times")
        try:
            deploy_hash = self.Contract.deploy_ckb_contract(
                account, path, enable_type_id=True, api_url=node.getClient().url
            )
            self.Miner.miner_until_tx_committed(node, deploy_hash)
            time.sleep(1)
            invoke_hash = self.Contract.invoke_ckb_contract(
                account_private=account,
                contract_out_point_tx_hash=deploy_hash,
                contract_out_point_tx_index=0,
                type_script_arg="0x02",
                data="0x1234",
                hash_type="type",
                api_url=node.getClient().url,
            )
            return invoke_hash
        except Exception as e:
            print(e)
            if "Resolve failed Dead" in str(e):
                try_count -= 1
                for i in range(2):
                    self.Miner.miner_with_version(node, "0x0")
                time.sleep(3)
                return self.deploy_and_invoke(account, path, node, try_count)
            if "PoolRejectedRBF" in str(e):
                try_count -= 1
                for i in range(2):
                    self.Miner.miner_with_version(node, "0x0")
                time.sleep(3)
                return self.deploy_and_invoke(account, path, node, try_count)
            raise e
