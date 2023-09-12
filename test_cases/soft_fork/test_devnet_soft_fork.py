from framework.basic import CkbTest


class TestDevNetSoftFork(CkbTest):
    def setup_method(self, method):
        pass

    def teardown_method(self, method):
        pass

    node: CkbTest.CkbNode

    @classmethod
    def setup_class(cls):
        node1 = cls.CkbNode.init_dev_by_port(cls.CkbNodeConfigPath.CURRENT_TEST, "tx_pool_test/node1", 8114,
                                             8227)
        cls.node = node1
        node1.prepare()
        node1.start()

    @classmethod
    def teardown_class(cls):
        print("\nTeardown TestClass1")
        cls.node.stop()
        cls.node.clean()

    def test_01_get_consensus(self):
        """
        rfc0043 min_activation_epoch  is 0x0
        1. query  get_consensus
        return consensus['softforks']['light_client']['rfc0043']['min_activation_epoch'] == "0x0"
        :return:
        """
        consensus = self.node.getClient().get_consensus()
        print(consensus)
        assert consensus['softforks']['light_client']['rfc0043']['min_activation_epoch'] == "0x0"

    def test_02_get_deployments_info(self):
        """
        rfc0043 is active in block :0
        1. query tip number
            return 0
        2. query get_deployments_info
            info['deployments']['light_client']['state'] == 'active'
        :return:
        """
        tip_number = self.node.getClient().get_tip_block_number()
        assert tip_number == 0
        info = self.node.getClient().get_deployments_info()
        assert info['deployments']['light_client']['state'] == 'active'

    def test_03_get_block_tmp(self):
        """
        block template contains extension
        1. query get_block_template
            template['extension'] is not None
        :return:
        """
        template = self.node.getClient().get_block_template()
        assert template['extension'] is not None
