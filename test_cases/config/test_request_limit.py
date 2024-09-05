import pytest

from framework.basic import CkbTest


class TestRequestLimit(CkbTest):
    node: CkbTest.CkbNode

    @classmethod
    def setup_class(cls):
        cls.node = cls.CkbNode.init_dev_by_port(
            cls.CkbNodeConfigPath.CURRENT_TEST, "node/node", 8118, 8119
        )
        cls.node.prepare()
        cls.node.start()
        # miner 100 block
        cls.Miner.make_tip_height_number(cls.node, 100)

    @classmethod
    def teardown_class(cls):
        cls.node.stop()
        cls.node.clean()


    def test_request_limit(self):
        """
        1. change ckb_request_limit = 10 in ckb.toml
        2. get_cells(len:0xff) => Invalid params limit must be less than 10
        3. get_cells(len:10) =>  cells.length = 10
        Returns:

        """

        # 1. change ckb_request_limit = 10 in ckb.toml
        self.node.stop()
        self.node.prepare(other_ckb_config={"ckb_request_limit": 10})
        self.node.start()

        # 2. get_cells(len:0xff) => Invalid params limit must be less than 10
        with pytest.raises(Exception) as exc_info:
            self.node.getClient().get_cells(
                {

                    "script": {
                        "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
                        "hash_type": "type",
                        "args": "0x",
                    },
                    "script_type": "lock",
                    "script_search_mode": "prefix",
                },
                "asc",
                "0xff",
                None,
            )
        expected_error_message = "Invalid params limit must be less than 10"
        assert (
            expected_error_message in exc_info.value.args[0]
        ), f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

        # 3. get_cells(len:10) =>  cells.length = 10
        cells = self.node.getClient().get_cells(
            {
                "script": {
                    "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
                    "hash_type": "type",
                    "args": "0x",
                },
                "script_type": "lock",
                "script_search_mode": "prefix",
            },
            "asc",
            "0xa",
            None,
        )
        assert len(cells["objects"]) == 10
