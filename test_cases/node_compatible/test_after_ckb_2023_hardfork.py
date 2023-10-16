import time

import pytest

from framework.basic import CkbTest

class TestAfterCkb2023(CkbTest):

    node_current = CkbTest.CkbNode.init_dev_by_port(CkbTest.CkbNodeConfigPath.CURRENT_TEST,
                                                    "node_compatible/current/node1", 8115,
                                                    8225)
    node_111 = CkbTest.CkbNode.init_dev_by_port(CkbTest.CkbNodeConfigPath.V111,
                                                "node_compatible/current/node2",
                                                8116,
                                                8226)
    node_110 = CkbTest.CkbNode.init_dev_by_port(CkbTest.CkbNodeConfigPath.V110, "node_compatible/current/node3", 8117,
                                                8227)
    nodes = [node_current, node_111, node_110]
    lt_111_nodes = [node_110]
    ge_111_nodes = [node_current, node_111]
    cluster: CkbTest.Cluster = CkbTest.Cluster(nodes)

    @classmethod
    def setup_class(cls):
        cls.cluster.prepare_all_nodes(
            other_ckb_config={'ckb_logger_filter': 'debug'}
        )
        cls.cluster.start_all_nodes()
        cls.node_current.connected(cls.node_111)
        cls.node_current.connected(cls.node_110)
        contracts = cls.Contract_util.deploy_contracts(cls.Config.ACCOUNT_PRIVATE_1, cls.cluster.ckb_nodes[0])
        cls.spawn_contract = contracts["SpawnContract"]
        cls.Miner.make_tip_height_number(cls.node_current, 900)
        cls.Node.wait_cluster_sync_with_miner(cls.cluster, 300, 900)
        heights = cls.cluster.get_all_nodes_height()
        print(f"heights:{heights}")
        cls.Miner.make_tip_height_number(cls.node_current, 1100)

    @classmethod
    def teardown_class(cls):
        print("\nTeardown TestClass1")
        heights = cls.cluster.get_all_nodes_height()
        print(heights)
        cls.cluster.stop_all_nodes()
        cls.cluster.clean_all_nodes()

    def test_01_lt_111_sync_hard_fork(self):
        self.Node.wait_node_height(self.node_110, 990, 100)
        time.sleep(10)
        tip_number = self.node_110.getClient().get_tip_block_number()
        assert tip_number <= 999

    def test_02_lt_111_sync_failed(self):
        node = self.CkbNode.init_dev_by_port(self.CkbNodeConfigPath.V110, "node_compatible/current/node5", 8229,
                                             8339)
        node.prepare()
        node.start()
        node.connected(self.node_current)
        self.cluster.ckb_nodes.append(node)
        with pytest.raises(Exception) as exc_info:
            self.Node.wait_node_height(node, 1, 30)
        expected_error_message = "time out"
        assert expected_error_message in exc_info.value.args[0], \
            f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

    def test_03_sync_successful_ge_111(self):
        node = self.CkbNode.init_dev_by_port(self.CkbNodeConfigPath.V111, "node_compatible/current/node6", 8129,
                                             8239)
        node.prepare()
        node.start()
        node.connected(self.node_current)
        self.Node.wait_node_height(node, 1001, 1000)
        self.cluster.ckb_nodes.append(node)
