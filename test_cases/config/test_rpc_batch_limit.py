import pytest

from framework.basic import CkbTest
from framework.util import run_command


class TestRpcBatchLimit(CkbTest):
    node: CkbTest.CkbNode

    @classmethod
    def setup_class(cls):
        cls.node = cls.CkbNode.init_dev_by_port(
            cls.CkbNodeConfigPath.CURRENT_TEST, "node/node", 8118, 8119
        )
        cls.node.prepare()
        cls.node.start()

    @classmethod
    def teardown_class(cls):
        cls.node.stop()
        cls.node.clean()
        pass

    def test_rpc_batch_limit(self):
        """
        1. set ckb_rpc_batch_limit = 10 in ckb.toml
        2. curl batch [11] -> batch size is too large, expect it less than: 10
        3. curl batch [10] -> successful
        Returns:

        """
        # 1. set ckb_rpc_batch_limit = 10 in ckb.toml
        self.node.stop()
        self.node.prepare(other_ckb_config={"ckb_rpc_batch_limit": 10})
        self.node.start()

        # 2. curl batch [11] -> batch size is too large, expect it less than: 10
        requestBody = ""
        for i in range(11):
            requestBody = (
                    requestBody
                    + """{"jsonrpc": "2.0", "method": "get_block_by_number", "params": ["0x0"], 
                        "id": "1"},"""
            )
        requestBody = requestBody[:-1]
        requests = (
                """curl -X POST -H "Content-Type: application/json" -d '["""
                + str(requestBody)
                + f"""]' {self.node.rpcUrl} """
        )
        response = run_command(requests)
        assert "batch size is too large, expect it less than: 10" in response

        # 3. curl batch [10] -> successful
        requestBody = ""
        for i in range(10):
            requestBody = (
                    requestBody
                    + """{"jsonrpc": "2.0", "method": "get_block_by_number", "params": ["0x0"], 
                                "id": "1"},"""
            )
        requestBody = requestBody[:-1]
        requests = (
                """curl -X POST -H "Content-Type: application/json" -d '["""
                + str(requestBody)
                + f"""]' {self.node.rpcUrl} """
        )
        response = run_command(requests)
        assert "batch size is too large, expect it less than: 10" not in response
