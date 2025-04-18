import time

import pytest

from framework.basic import CkbTest
from framework.util import get_project_root


class TestIpcWithOutIndexer(CkbTest):

    @classmethod
    def setup_class(cls):
        """
        1. start node in issue/node1
        2. generate 2 epoch
        Returns:

        """

        # 1. start node in issue/node1
        node1 = cls.CkbNode.init_dev_by_port(
            cls.CkbNodeConfigPath.CURRENT_TEST, "ipc_call/node1", 8114, 8927
        )
        cls.node = node1
        node1.prepare(
            other_ckb_config={
                "ckb_rpc_modules": [
                    "Net",
                    "Pool",
                    "Miner",
                    "Chain",
                    "Stats",
                    "Subscription",
                    "Experiment",
                    "Debug",
                    "IntegrationTest",
                    "IPC",
                ]
            }
        )
        node1.start()

        # 2. miner 400 block
        # cls.Miner.make_tip_height_number(cls.node, 400)
        cls.node.getClient().generate_epochs("0x2")
        time.sleep(3)
        cls.ipc_test_contract_tx_hash = cls.Contract.deploy_ckb_contract(
            cls.Config.ACCOUNT_PRIVATE_1,
            f"{get_project_root()}/source/contract/ipc_test/ipc_test",
        )
        cls.Miner.miner_until_tx_committed(cls.node, cls.ipc_test_contract_tx_hash)

    @classmethod
    def teardown_class(cls):
        print("\nTeardown TestClass1")
        cls.node.stop()
        cls.node.clean()

    def test_type_id_args_without_indexer(self):
        """
        没开启index模块，IpcScriptLocator 使用type_id_args 模式,报错：Query by type id requires enabling Indexer
        Returns:

        """
        tx = self.node.getClient().get_transaction(self.ipc_test_contract_tx_hash)
        ipc_script_locator = {
            "type_id_args": tx["transaction"]["outputs"][0]["type"]["args"],
        }
        ipc_req = {
            "version": "0x0",
            "method_id": "0x0",
            "payload_format": "json",
            "payload": {
                "MathAdd": {"a": 2, "b": 1},
            },
        }
        ipc_ret = self.node.getClient().ipc_call(ipc_script_locator, ipc_req)
        print(f"main: call result json={ipc_ret}")
        assert ipc_ret["payload"]["MathAdd"] == 3
        self.node.stop()
        self.node.start_without_indexer()

        with pytest.raises(Exception) as exc_info:
            ipc_ret = self.node.getClient().ipc_call(ipc_script_locator, ipc_req)
        expected_error_message = "Query by type id requires enabling Indexer"
        assert (
            expected_error_message in exc_info.value.args[0]
        ), f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"
