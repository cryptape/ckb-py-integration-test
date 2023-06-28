import time

from framework.test_cluster import Cluster
from framework.test_node import CkbNode, CkbNodeConfigPath


class TestCluster:

    @classmethod
    def setup_class(cls):
        nodes = [
            CkbNode.init_dev_by_port(CkbNodeConfigPath.CURRENT_TEST, "cluster/node{i}".format(i=i), 8114 + i, 8225 + i)
            for
            i in range(1, 5)]
        cls.cluster = Cluster(nodes)
        cls.cluster.prepare_all_nodes()
        cls.cluster.start_all_nodes()

    @classmethod
    def teardown_class(cls):
        print("\nTeardown TestClass1")
        cls.cluster.stop_all_nodes()
        cls.cluster.clean_all_nodes()

    def test_01_link_node(self):
        self.cluster.connected_node(0, 1)
        self.cluster.ckb_nodes[0].start_miner()
        wait_node_height(self.cluster.ckb_nodes[1], 10, 100)
        heights = self.cluster.get_all_nodes_height()
        assert heights[0] > 0
        assert heights[1] > 0
        assert heights[2] == 0
        assert heights[3] == 0


def wait_node_height(node: CkbNode, num, wait_times):
    for i in range(wait_times):
        if node.getClient().get_tip_block_number() > num:
            return
        time.sleep(1)
    raise Exception("time out ,node tip number:{number}".format(number=node.getClient().get_tip_block_number()))
