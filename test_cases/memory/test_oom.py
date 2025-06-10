import time

import pytest

from framework.basic import CkbTest
from framework.util import get_project_root


class TestOom(CkbTest):

    @classmethod
    def setup_class(cls):
        cls.node = cls.CkbNode.init_dev_by_port(
            cls.CkbNodeConfigPath.CURRENT_TEST, "contract/node1", 8116, 8115
        )
        cls.node119 = cls.CkbNode.init_dev_by_port(
            cls.CkbNodeConfigPath.v120, "contract/node2", 8117, 8118
        )
        cls.node119.prepare(
            # {"ckb_logger_filter": "debug"}
        )
        cls.node119.start()
        cls.node.prepare(
            # {"ckb_logger_filter": "debug"}
        )
        cls.node.start()
        cls.Miner.make_tip_height_number(cls.node, 2000)
        cls.node.getClient().generate_epochs("0x2")
        cls.node119.connected(cls.node)
        tip_number = cls.node.getClient().get_tip_block_number()
        cls.Node.wait_node_height(cls.node119, tip_number, 1000)

    @classmethod
    def teardown_class(cls):
        cls.node.stop()
        cls.node.clean()
        cls.node119.stop()
        cls.node119.clean()

    def test_spawn(self):
        with pytest.raises(Exception) as exc_info:
            self.deploy_and_invoke(self.Config.ACCOUNT_PRIVATE_1,
                                   f"{get_project_root()}/source/contract/test_cases/spawn_oom",
                                   self.node,"type"
                                   )
        expected_error_message = "MemOutOfStack"
        # expected_error_message = "@@@VM@@@UNEXPECTED@@@ARGV@@@TOOLONG@@@"
        assert expected_error_message in exc_info.value.args[0], (
            f"Expected substring '{expected_error_message}' "
            f"not found in actual string '{exc_info.value.args[0]}'"
        )

    def test_exec(self):
        with pytest.raises(Exception) as exc_info:
            self.deploy_and_invoke(self.Config.ACCOUNT_PRIVATE_1,
                                   f"{get_project_root()}/source/contract/test_cases/exec_oom",
                                   self.node
                                   )
        expected_error_message = "@@@VM@@@UNEXPECTED@@@ARGV@@@TOOLONG@@@"
        assert expected_error_message in exc_info.value.args[0], (
            f"Expected substring '{expected_error_message}' "
            f"not found in actual string '{exc_info.value.args[0]}'"
        )

    def deploy_and_invoke(self, account, path, node, hash_type="data1", try_count=5):
        if try_count < 0:
            raise Exception("try out of times")
        try:
            deploy_hash = self.Contract.deploy_ckb_contract(
                account, path, enable_type_id=True, api_url=node.getClient().url
            )
            self.Miner.miner_until_tx_committed(node, deploy_hash)
            time.sleep(1)
            beginTime = time.time()
            invoke_hash = self.Contract.invoke_ckb_contract(
                account_private=account,
                contract_out_point_tx_hash=deploy_hash,
                contract_out_point_tx_index=0,
                type_script_arg="0x02",
                data="0x1234",
                hash_type=hash_type,
                api_url=node.getClient().url,
            )
            cost_time = time.time() - beginTime
            print("cost_time:", cost_time)
            tx = node.getClient().get_transaction(invoke_hash)
            del tx["transaction"]["hash"]
            self.node.getClient().clear_tx_pool()
            beginTime = time.time()
            self.node.getClient().test_tx_pool_accept(tx["transaction"], "passthrough")
            cost_time = time.time() - beginTime
            print("test_tx_pool_accept cost_time:", cost_time)
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
