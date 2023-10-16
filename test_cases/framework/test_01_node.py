import time

from framework.basic import CkbTest


class TestNode(CkbTest):

    @classmethod
    def setup_class(cls):
        cls.node = cls.CkbNode.init_dev_by_port(cls.CkbNodeConfigPath.CURRENT_TEST, "node/node", 8114, 8115)
        cls.node.prepare()
        cls.node.start()

    @classmethod
    def teardown_class(cls):
        cls.node.stop()
        cls.node.clean()

    def test_01_miner(self):
        time.sleep(10)
        self.node.start_miner()
        time.sleep(10)
        tip_number = self.node.getClient().get_tip_block_number()
        assert tip_number > 0
