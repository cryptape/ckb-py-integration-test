from framework.basic import CkbTest


class TestMainNetSoftForkFailed(CkbTest):

    @classmethod
    def setup_class(cls):
        node1 = cls.CkbNode.init_dev_by_port(cls.CkbNodeConfigPath.CURRENT_MAIN, "tx_pool_main/node1", 8119,
                                         8227)
        node2 = cls.CkbNode.init_dev_by_port(cls.CkbNodeConfigPath.V109_MAIN, "tx_pool_main/node2", 8120, 8228)
        cls.cluster = cls.Cluster([node1, node2])
        cls.node = node1
        cls.node109 = node2

        node1.prepare(other_ckb_spec_config={"ckb_params_genesis_epoch_length": "1", "ckb_name": "ckb"})
        node2.prepare(other_ckb_spec_config={"ckb_params_genesis_epoch_length": "1", "ckb_name": "ckb"})
        cls.cluster.start_all_nodes()
        cls.cluster.connected_all_nodes()
        cls.Miner.make_tip_height_number(node2, 200)
        cls.Node.wait_cluster_height(cls.cluster, 100, 300)

    @classmethod
    def teardown_class(cls):
        print("\nTeardown TestClass1")
        cls.cluster.stop_all_nodes()
        cls.cluster.clean_all_nodes()

    def test_01_get_consensus_in_ge_110(self):
        """
        > 110 node softforks:light_client min_activation_epoch ==  0x21c8
        > 110 node softforks:light_client start == 0x205a
        > 110 node softforks:light_client timeout == 0x2168
        1. query get_consensus
        :return:
        """
        consensus = self.node.getClient().get_consensus()
        assert consensus['softforks']['light_client']['rfc0043']['min_activation_epoch'] == '0x21c8'
        assert consensus['softforks']['light_client']['rfc0043']['start'] == '0x205a'
        assert consensus['softforks']['light_client']['rfc0043']['timeout'] == '0x2168'

    def test_02_get_consensus_in_lt_110(self):
        """
        < 110 node  softforks == {}
        :return:
        """
        consensus = self.node109.getClient().get_consensus()
        assert consensus['softforks'] == {}

    def test_03_get_deployments_in_gt_110(self):
        """
        > 110 node deployments:light_client min_activation_epoch ==  0x21c8
        > 110 node deployments:light_client period == 0x2a
        > 110 node deployments:light_client timeout == 0x2168
        1. query get_deployments_info
        :return:
        """
        deployments = self.node.getClient().get_deployments_info()
        assert deployments['deployments']['light_client']['min_activation_epoch'] == '0x21c8'
        assert deployments['deployments']['light_client']['period'] == '0x2a'
        assert deployments['deployments']['light_client']['timeout'] == '0x2168'

    def test_04_miner_use_109(self):
        """
        use 109 miner block,will cause softfork failed
        1. 109 node miner to 8314
            query 110 node statue == defined
        2. 109 node miner to 8915
            query 110 node statue == started
        3. 109 node miner to 8566
            query 110 node statue == started
        4. 109 node miner to 8567
            query 110 node statue == failed
        :return:
        """
        self.Miner.make_tip_height_number(self.node109, 8314)
        self.Node.wait_node_height(self.node, 8314, 100)
        deployments_info = self.node.getClient().get_deployments_info()
        assert deployments_info['deployments']['light_client']['state'] == "defined"
        self.Miner.make_tip_height_number(self.node109, 8315)
        self.Node.wait_node_height(self.node, 8315, 100)
        deployments_info = self.node.getClient().get_deployments_info()
        assert deployments_info['deployments']['light_client']['state'] == "started"
        self.Miner.make_tip_height_number(self.node109, 8566)
        self.Node.wait_node_height(self.node, 8566, 100)
        deployments_info = self.node.getClient().get_deployments_info()
        assert deployments_info['deployments']['light_client']['state'] == "started"
        self.Miner.make_tip_height_number(self.node109, 8567)
        self.Node.wait_node_height(self.node, 8567, 100)
        deployments_info = self.node.getClient().get_deployments_info()
        assert deployments_info['deployments']['light_client']['state'] == "failed"
