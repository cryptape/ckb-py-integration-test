import time

from framework.basic import CkbTest
from test_cases.rpc.node_fixture import get_cluster


class TestGetTransaction:

    def test_query_tx_only_commit_is_true(self, get_cluster):
        """
        https://github.com/nervosnetwork/ckb/pull/3963
        pending tx
        - enable committed: tx_status = uni
        - not enable committed : tx_status = pending

        proposed tx
        - enable committed: tx_status = unknown
        - not enable committed : tx_status = proposed

        committed tx
        - enable committed: tx_status = committed
        - not enable committed : tx_status = committed
        :return:
        """
        cluster = get_cluster
        account1 = CkbTest.Ckb_cli.util_key_info_by_private_key(CkbTest.Config.ACCOUNT_PRIVATE_1)
        tx_hash = CkbTest.Ckb_cli.wallet_transfer_by_private_key(CkbTest.Config.ACCOUNT_PRIVATE_1,
                                                              account1["address"]["testnet"],
                                                              140,
                                                              cluster.ckb_nodes[0].client.url)

        # pending tx
        response_enable_commit = cluster.ckb_nodes[0].getClient().get_transaction(tx_hash, None, True)
        response = cluster.ckb_nodes[0].getClient().get_transaction(tx_hash, None, False)
        assert response['tx_status']['status'] == "pending"
        assert response_enable_commit['tx_status']['status'] == "unknown"

        # proposed tx
        for i in range(100):
            response = cluster.ckb_nodes[0].getClient().get_transaction(tx_hash, None, False)
            if response['tx_status']['status'] == "proposed":
                break
            if response['tx_status']['status'] == "committed":
                response_enable_commit = cluster.ckb_nodes[0].getClient().get_transaction(tx_hash, None, True)
                response = cluster.ckb_nodes[0].getClient().get_transaction(tx_hash, None, True)
                assert response_enable_commit['tx_status']['status'] == "committed"
                assert response['tx_status']['status'] == "committed"
                return
            CkbTest.Miner.miner_with_version(cluster.ckb_nodes[0], "0x0")
            time.sleep(1)
        response_enable_commit = cluster.ckb_nodes[0].getClient().get_transaction(tx_hash, None, True)
        response = cluster.ckb_nodes[0].getClient().get_transaction(tx_hash, None, False)
        assert response['tx_status']['status'] == "proposed"
        assert response_enable_commit['tx_status']['status'] == "unknown"

        # committed tx
        for i in range(100):
            response = cluster.ckb_nodes[0].getClient().get_transaction(tx_hash, None, False)
            if response['tx_status']['status'] == "committed":
                break
            CkbTest.Miner.miner_with_version(cluster.ckb_nodes[0], "0x0")
            time.sleep(1)
        response_enable_commit = cluster.ckb_nodes[0].getClient().get_transaction(tx_hash, None, True)
        response = cluster.ckb_nodes[0].getClient().get_transaction(tx_hash, None, True)
        assert response_enable_commit['tx_status']['status'] == "committed"
        assert response['tx_status']['status'] == "committed"

    def test_query_tx_without_only_commit(self, get_cluster):
        """
        only_commit is None
        - use default only_commit = False
        :return:
        """
        cluster = get_cluster
        account1 = CkbTest.Ckb_cli.util_key_info_by_private_key(CkbTest.Config.ACCOUNT_PRIVATE_1)
        tx_hash = CkbTest.Ckb_cli.wallet_transfer_by_private_key(CkbTest.Config.ACCOUNT_PRIVATE_1,
                                                              account1["address"]["testnet"],
                                                              140,
                                                              cluster.ckb_nodes[0].client.url)

        # pending tx
        response_use_default = cluster.ckb_nodes[0].getClient().get_transaction(tx_hash)
        response = cluster.ckb_nodes[0].getClient().get_transaction(tx_hash, None, False)
        assert response['tx_status']['status'] == "pending"
        assert response_use_default['tx_status']['status'] == "pending"
        CkbTest.Miner.miner_until_tx_committed(cluster.ckb_nodes[0], tx_hash)
