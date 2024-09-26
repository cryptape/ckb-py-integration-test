import pytest

from framework.basic import CkbTest
from framework.helper.miner import block_template_transfer_to_submit_block


class TestMinerWrongWitness(CkbTest):

    @classmethod
    def setup_class(cls):
        cls.node = cls.CkbNode.init_dev_by_port(
            cls.CkbNodeConfigPath.CURRENT_TEST, "node/node", 8114, 8115
        )
        cls.node.prepare()
        cls.node.start()

    @classmethod
    def teardown_class(cls):
        cls.node.stop()
        cls.node.clean()

    def test_01(self):
        """
        1. submit_block wrong witness
        2. return error
        Returns:

        """
        block = self.node.getClient().get_block_template()
        # InvalidWitness
        with pytest.raises(Exception) as exc_info:
            block["cellbase"]["data"]["witnesses"][
                0
            ] = "0x7a0000000c00000055000000490000001000000030000000310000009bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce814140000008883a512ee2383c01574a328f60eeccbb4d78240210000000000000020302e3131382e3020286366643861376620323032342d30392d323229"
            self.node.getClient().submit_block(
                block["work_id"], block_template_transfer_to_submit_block(block, "0x0")
            )
        expected_error_message = "InvalidWitness"
        assert (
            expected_error_message in exc_info.value.args[0]
        ), f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"
