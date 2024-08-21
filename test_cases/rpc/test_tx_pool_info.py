from test_cases.rpc.node_fixture import get_cluster_indexer


class TestTxPoolInfo:

    def test_tx_pool_info(self, get_cluster_indexer):
        cluster = get_cluster_indexer
        pool_info = cluster.ckb_nodes[0].getClient().tx_pool_info()
        assert pool_info["verify_queue_size"] == "0x0"
