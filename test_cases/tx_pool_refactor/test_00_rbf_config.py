import pytest

from framework.basic import CkbTest


class TestRBFConfig(CkbTest):
    @classmethod
    def setup_class(cls):
        cls.node = cls.CkbNode.init_dev_by_port(cls.CkbNodeConfigPath.CURRENT_TEST, "tx_pool/node1", 8120,
                                                8225)
        cls.node.prepare(other_ckb_config={"ckb_tx_pool_min_rbf_rate": "800"})
        cls.node.start()
        cls.Miner.make_tip_height_number(cls.node, 30)

    @classmethod
    def teardown_class(cls):
        cls.node.stop()
        cls.node.clean()

    def test_transaction_replacement_disabled_failure(self):
        """
        Disabling RBF (Replace-By-Fee) feature, transaction replacement fails.
        1. starting the node, modify ckb.toml with min_rbf_rate = 800 < min_fee_rate.
            node starts successfully.
        2. send tx use same input cell
            ERROR:  TransactionFailedToResolve: Resolve failed Dead
        :return:
        """

        account = self.Ckb_cli.util_key_info_by_private_key(self.Config.MINER_PRIVATE_1)

        self.Ckb_cli.wallet_transfer_by_private_key(self.Config.MINER_PRIVATE_1, account["address"]["testnet"], 100,
                                                    self.node.getClient().url, "1500")

        with pytest.raises(Exception) as exc_info:
            self.Ckb_cli.wallet_transfer_by_private_key(self.Config.MINER_PRIVATE_1, account["address"]["testnet"], 200,
                                                        self.node.getClient().url, "2000")
        expected_error_message = " TransactionFailedToResolve: Resolve failed Dead"
        assert expected_error_message in exc_info.value.args[0], \
            f"Expected substring '{expected_error_message}' " \
            f"not found in actual string '{exc_info.value.args[0]}'"

    def test_disable_rbf_and_check_min_replace_fee(self):
        """
        Disabling RBF (Replace-By-Fee) feature, transaction min_replace_fee is null
         1. starting the node, modify ckb.toml with min_rbf_rate = 800 < min_fee_rate.
            node starts successfully.
        2. send tx and get_transaction
            min_rbf_rate == null
        :return:
        """
        account = self.Ckb_cli.util_key_info_by_private_key(self.Config.ACCOUNT_PRIVATE_1)

        tx = self.Ckb_cli.wallet_transfer_by_private_key(self.Config.ACCOUNT_PRIVATE_1, account["address"]["testnet"],
                                                         100,
                                                         self.node.getClient().url, "1500")
        transaction = self.node.getClient().get_transaction(tx)
        assert transaction['fee'] is not None
        assert transaction['min_replace_fee'] is None
