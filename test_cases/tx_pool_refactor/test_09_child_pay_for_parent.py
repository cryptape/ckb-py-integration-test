import pytest

from framework.basic import CkbTest


class TestRbfChildPayForParent(CkbTest):

    @classmethod
    def setup_class(cls):
        cls.node = cls.CkbNode.init_dev_by_port(cls.CkbNodeConfigPath.CURRENT_TEST, "tx_pool/node1", 8120,
                                                8225)
        cls.node.prepare()
        cls.node.start()
        cls.Miner.make_tip_height_number(cls.node, 30)

    @classmethod
    def teardown_class(cls):
        cls.node.stop()
        cls.node.clean()

    def test_child_big_fee(self):
        """
        1. send tx1-1(fee:1000)
        2. send tx1-1-1(fee:10000)
        3. send tx1-2(fee:2000)
            return error
        """
        # 1. send tx1
        account = self.Ckb_cli.util_key_info_by_private_key(self.Config.ACCOUNT_PRIVATE_1)
        tx1_hash = self.Ckb_cli.wallet_transfer_by_private_key(self.Config.ACCOUNT_PRIVATE_1,
                                                               account["address"]["testnet"], 100,
                                                               self.node.getClient().url, "1500")
        print("send tx1_hash:", tx1_hash)
        # 1. send tx11(fee:1000)
        tx11_hash = self.Tx.send_transfer_self_tx_with_input([tx1_hash], ["0x0"], self.Config.ACCOUNT_PRIVATE_1,
                                                             fee=1000, output_count=1,
                                                             api_url=self.node.getClient().url)
        print("send tx11_hash:", tx11_hash)

        # 2. send tx 111(fee:10000)
        tx111_hash = self.Tx.send_transfer_self_tx_with_input([tx11_hash], ["0x0"], self.Config.ACCOUNT_PRIVATE_1,
                                                              fee=10000000,
                                                              api_url=self.node.getClient().url)
        print("send tx111_hash:", tx111_hash)

        # 3. send tx 12(fee:2000)
        with pytest.raises(Exception) as exc_info:
            tx12_hash = self.Tx.send_transfer_self_tx_with_input([tx1_hash], ["0x0"], self.Config.ACCOUNT_PRIVATE_1,
                                                                 fee=2000,
                                                                 api_url=self.node.getClient().url)
        expected_error_message = "Server error: PoolRejectedRBF: RBF rejected: Tx's current fee is 2000, expect it to " \
                                 ">= 10001532 to replace old txs"
        assert expected_error_message in exc_info.value.args[0], \
            f"Expected substring '{expected_error_message}' " \
            f"not found in actual string '{exc_info.value.args[0]}'"
