from framework.basic import CkbTest
import pytest


class TestGetLiveCell(CkbTest):

    @classmethod
    def setup_class(cls):
        cls.node = cls.CkbNode.init_dev_by_port(cls.CkbNodeConfigPath.CURRENT_TEST, "tx_pool/node1", 8120,
                                                8225)
        cls.node.prepare(other_ckb_config={"ckb_tx_pool_max_tx_pool_size": "180_000"})
        cls.node.start()
        cls.Miner.make_tip_height_number(cls.node, 100)

    @classmethod
    def teardown_class(cls):
        cls.node.stop()
        cls.node.clean()

    @pytest.mark.skip("wait v116.1 release")
    def test_get_live_cell(self):
        account = self.Ckb_cli.util_key_info_by_private_key(self.Config.MINER_PRIVATE_1)
        tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(self.Config.MINER_PRIVATE_1,
                                                              account["address"]["testnet"], 100,
                                                              self.node.getClient().url, "1500")
        print(f"txHash:{tx_hash}")
        transaction = self.node.getClient().get_transaction(tx_hash)
        result = self.node.getClient().get_live_cell_with_include_tx_pool(
            transaction["transaction"]["inputs"][0]["previous_output"]["index"],
            transaction["transaction"]["inputs"][0]["previous_output"]["tx_hash"])
        assert result['status'] == 'live'
        result = self.node.getClient().get_live_cell(
            transaction["transaction"]["inputs"][0]["previous_output"]["index"],
            transaction["transaction"]["inputs"][0]["previous_output"]["tx_hash"], include_tx_pool=True)
        assert result['status'] == 'live'
        remove_result = self.node.getClient().remove_transaction(tx_hash)
        assert remove_result == True
        result = self.node.getClient().get_live_cell(
            transaction["transaction"]["inputs"][0]["previous_output"]["index"],
            transaction["transaction"]["inputs"][0]["previous_output"]["tx_hash"], include_tx_pool=False)
        assert result['status'] == 'live'
