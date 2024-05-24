from test_cases.rpc.node_fixture import get_cluster
from framework.basic import CkbTest


class TestGetPoolTxDetailInfo():

    def test_get_pooltx_info(self, get_cluster):
        # After sending the transaction, immediately call 'get_pool_tx_detail_info' to query.
        cluster = get_cluster
        account1 = CkbTest.Ckb_cli.util_key_info_by_private_key(CkbTest.Config.ACCOUNT_PRIVATE_1)
        tx_hash = CkbTest.Ckb_cli.wallet_transfer_by_private_key(CkbTest.Config.ACCOUNT_PRIVATE_1,
                                                                 account1["address"]["testnet"],
                                                                 140,
                                                                 cluster.ckb_nodes[0].client.url)
        pooltx_info = cluster.ckb_nodes[0].getClient().get_pool_tx_detail_info(tx_hash)
        assert pooltx_info['entry_status'] == 'pending'
