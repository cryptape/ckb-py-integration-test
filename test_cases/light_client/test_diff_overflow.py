import pytest

from framework.basic import CkbTest


class TestDiffOverflow(CkbTest):

    node: CkbTest.CkbNode
    cluster: CkbTest.Cluster
    ckb_light_node: CkbTest.CkbLightClientNode

    @classmethod
    def setup_class(cls):
        node1 = cls.CkbNode.init_dev_by_port(cls.CkbNodeConfigPath.V110_MAIN, "tx_pool_main/node1", 8115,
                                             8227)
        node2 = cls.CkbNode.init_dev_by_port(cls.CkbNodeConfigPath.V110_MAIN, "tx_pool_main/node2", 8116,
                                             8228)

        cls.node = node1
        cls.node2 = node2
        cls.cluster = cls.Cluster([node1, node2])
        node1.prepare(other_ckb_spec_config={"ckb_params_genesis_epoch_length": "1", "ckb_name": "ckb_dev",
                                             "ckb_params_genesis_compact_target": "0x2020000"})
        node2.prepare(other_ckb_spec_config={"ckb_params_genesis_epoch_length": "1", "ckb_name": "ckb_dev",
                                             "ckb_params_genesis_compact_target": "0x2020000"})

        cls.cluster.start_all_nodes()
        cls.cluster.connected_all_nodes()
        cls.Miner.make_tip_height_number(cls.node, 5)
        cls.Node.wait_cluster_height(cls.cluster, 5, 1000)
        cls.ckb_light_node = cls.CkbLightClientNode.init_by_nodes(cls.CkbLightClientConfigPath.CURRENT_TEST, [cls.node],
                                                                  "tx_pool_light/node1", 8001)

        cls.account = cls.Ckb_cli.util_key_info_by_private_key(cls.Config.MINER_PRIVATE_1)

        cls.ckb_light_node.prepare()
        cls.ckb_light_node.start()
        cls.ckb_light_node.getClient().set_scripts([{"script": {
            "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8", "hash_type": "type",
            "args": cls.account['lock_arg']}, "script_type": "lock", "block_number": "0x0"}])

    @classmethod
    def teardown_class(cls):
        print("\nTeardown TestClass1")
        cls.node.stop()
        cls.node.clean()
        cls.node2.stop()
        cls.node2.clean()
        cls.ckb_light_node.stop()
        cls.ckb_light_node.clean()

    def test_light_node_when_diff_very_big(self):
        """
        ckb-light-client sync  successful  when diff very big
        1. wait ckb-light-client sync 5 block
        2. node2 close net
        3. node2 miner 500 block(500 epoch )
        4. node2 start net
        5. wait node1 sync 500 block
        6. wait ckb-light-client sync 500 block
        Returns:

        """
        self.Node.wait_light_sync_height(self.ckb_light_node, 5, 3000)
        self.node2.getClient().set_network_active(False)
        self.Miner.make_tip_height_number(self.node2, 500)
        self.node2.getClient().set_network_active(True)
        self.Node.wait_node_height(self.node, 500, 1000)
        self.Node.wait_light_sync_height(self.ckb_light_node, 500, 30000)
