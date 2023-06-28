from framework.test_node import CkbNode
from framework.test_cluster import Cluster
import time


def wait_node_height(node: CkbNode, num, wait_times):
    for i in range(wait_times):
        if node.getClient().get_tip_block_number() >= num:
            return
        time.sleep(1)
    raise Exception("time out ,node tip number:{number}".format(number=node.getClient().get_tip_block_number()))


def wait_cluster_height(cluster: Cluster, num, wait_times):
    for ckb_node in cluster.ckb_nodes:
        wait_node_height(ckb_node, num, wait_times)
