from framework.config import MINER_PRIVATE_1
from framework.helper.ckb_cli import util_key_info_by_private_key
from framework.helper.miner import make_tip_height_number
from framework.helper.node import wait_cluster_height, wait_light_sync_height
from framework.test_light_client import CkbLightClientNode, CkbLightClientConfigPath
from framework.test_node import CkbNode, CkbNodeConfigPath
from framework.test_cluster import Cluster


class TestMainnetSoftForkWithCkbLightClient:
    node: CkbNode
    cluster: Cluster
    ckb_light_node: CkbLightClientNode

    @classmethod
    def setup_class(cls):
        node1 = CkbNode.init_dev_by_port(CkbNodeConfigPath.CURRENT_MAIN, "tx_pool_main/node1", 8115,
                                         8227)
        node2 = CkbNode.init_dev_by_port(CkbNodeConfigPath.CURRENT_MAIN, "tx_pool_main/node2", 8116,
                                         8228)
        cls.node = node1
        cls.cluster = Cluster([node1, node2])
        node1.prepare(other_ckb_spec_config={"ckb_params_genesis_epoch_length": "1", "ckb_name": "ckb"})
        node2.prepare(other_ckb_spec_config={"ckb_params_genesis_epoch_length": "1", "ckb_name": "ckb"})
        cls.cluster.start_all_nodes()
        cls.cluster.connected_all_nodes()
        make_tip_height_number(cls.node, 200)
        wait_cluster_height(cls.cluster, 100, 300)
        cls.ckb_light_node = CkbLightClientNode.init_by_nodes(CkbLightClientConfigPath.V0_2_4, [cls.node],
                                                              "tx_pool_light/node1", 8001)

        cls.account = util_key_info_by_private_key(MINER_PRIVATE_1)

        cls.ckb_light_node.prepare()
        cls.ckb_light_node.start()
        cls.ckb_light_node.getClient().set_scripts([{"script": {
            "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8", "hash_type": "type",
            "args": cls.account['lock_arg']}, "script_type": "lock", "block_number": "0x0"}])

    @classmethod
    def teardown_class(cls):
        print("\nTeardown TestClass1")
        cls.cluster.stop_all_nodes()
        cls.cluster.clean_all_nodes()
        cls.ckb_light_node.stop()
        cls.ckb_light_node.clean()

    def test_soft_fork_activation_light_node(self):
        """
        Soft fork transitioning from 'defined' to 'active' will not
        affect the synchronization of light nodes.
        1. Mine until block 10000.
            Successful.
        2. Wait for light nodes to synchronize up to block 10000.
            Successful.
        3. Query the balance of the mining address.
            Light node == node.
        :return:
        """
        make_tip_height_number(self.node, 10000)
        wait_cluster_height(self.cluster, 10000, 300)
        height = self.cluster.get_all_nodes_height()
        assert height[0] == height[1]
        wait_light_sync_height(self.ckb_light_node, height[0], 3000)
        node_res = self.cluster.ckb_nodes[0].getClient().get_cells_capacity({"script": {
            "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8", "hash_type": "type",
            "args": self.account['lock_arg']}, "script_type": "lock"})
        light_res = self.ckb_light_node.getClient().get_cells_capacity({"script": {
            "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8", "hash_type": "type",
            "args": self.account['lock_arg']}, "script_type": "lock"})
        assert int(node_res['capacity'], 16) == int(light_res['capacity'], 16)
