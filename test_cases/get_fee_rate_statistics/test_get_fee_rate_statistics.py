import pytest

from framework.basic import CkbTest


class TestGetFeeRateStatistics(CkbTest):

    @classmethod
    def setup_class(cls):
        cls.node = cls.CkbNode.init_dev_by_port(
            cls.CkbNodeConfigPath.CURRENT_TEST, "telnet1/node", 8114, 8115
        )
        cls.node.prepare()
        cls.node.start()
        cls.Miner.make_tip_height_number(cls.node, 50)

    @classmethod
    def teardown_class(cls):
        cls.node.stop()
        cls.node.clean()
        print("\nTeardown TestClass1")

    @pytest.mark.skip
    def test_01(self):
        # build Tx
        account1 = self.Ckb_cli.util_key_info_by_private_key(
            self.Config.ACCOUNT_PRIVATE_1
        )
        for i in range(5):
            tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(
                self.Config.ACCOUNT_PRIVATE_1,
                account1["address"]["testnet"],
                140,
                self.node.client.url,
                fee_rate=str(1000 * (i + 1)),
            )
            tx = self.node.getClient().get_pool_tx_detail_info(tx_hash)
            self.Miner.miner_until_tx_committed(self.node, tx_hash)
        ret = self.node.getClient().get_fee_rate_statics()
        assert ret["mean"] == "0xbb8"
        assert ret["median"] == "0xbb8"
