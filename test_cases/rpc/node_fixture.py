import os

import pytest

from framework.helper.miner import make_tip_height_number
from framework.helper.node import wait_cluster_height
from framework.test_cluster import Cluster
from framework.test_node import CkbNode, CkbNodeConfigPath
from framework.util import get_project_root

@pytest.fixture(scope='module')
def get_cluster():
    nodes = [
        CkbNode.init_dev_by_port(CkbNodeConfigPath.CURRENT_TEST, "cluster/hardfork/node{i}".format(i=i), 8114 + i,
                                 8225 + i)
        for
        i in range(1, 5)
    ]

    cluster = Cluster(nodes)
    cluster.prepare_all_nodes()
    cluster.start_all_nodes()
    cluster.connected_all_nodes()
    cluster.ckb_nodes[0].start_miner()
    make_tip_height_number(cluster.ckb_nodes[0], 1100)
    wait_cluster_height(cluster, 1100, 100)

    yield cluster
    print("\nTeardown TestClass1")
    cluster.stop_all_nodes()
    cluster.clean_all_nodes()
