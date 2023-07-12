from framework.test_node import CkbNode
from framework.test_cluster import Cluster
import time
from functools import wraps

def wait_until_timeout(wait_times):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for i in range(wait_times):
                if func(*args, **kwargs):
                    return
                time.sleep(1)
            raise Exception("Timeout reached")

        return wrapper

    return decorator


@wait_until_timeout(wait_times=60)
def wait_get_transaction(node, tx_hash, status):
    return node.getClient().get_transaction(tx_hash)['tx_status']['status'] == status


def wait_node_height(node: CkbNode, num, wait_times):
    for i in range(wait_times):
        if node.getClient().get_tip_block_number() >= num:
            return
        time.sleep(1)
    raise Exception("time out ,node tip number:{number}".format(number=node.getClient().get_tip_block_number()))


def wait_cluster_height(cluster: Cluster, num, wait_times):
    for ckb_node in cluster.ckb_nodes:
        wait_node_height(ckb_node, num, wait_times)



def wait_cluster_sync_with_miner(cluster: Cluster, wait_times,sync_number = None):
    """
    miner can make
    :param cluster:
    :param wait_times:
    :param sync_number:
    :return:
    """
    if sync_number is None:
        sync_number = cluster.ckb_nodes[0].getClient().get_tip_block_number()
    cluster.ckb_nodes[0].start_miner()
    wait_cluster_height(cluster, sync_number, wait_times)
    cluster.ckb_nodes[0].stop_miner()
