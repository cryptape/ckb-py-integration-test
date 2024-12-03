import pytest

from framework.basic import CkbTest


class Test4698(CkbTest):

    @classmethod
    def setup_class(cls):
        """
        1. start 1 ckb node in tmp/feature/TestTxPoolAccept/node1 dir
        2. miner 200 block
        Returns:

        """
        cls.node = cls.CkbNode.init_dev_by_port(
            cls.CkbNodeConfigPath.CURRENT_TEST,
            "feature/TestTxPoolAccept/node1",
            8114,
            8225,
        )
        cls.node.prepare(other_ckb_config={"ckb_tx_pool_max_tx_pool_size": "4640"})
        cls.node.start()
        cls.Miner.make_tip_height_number(cls.node, 200)

    @classmethod
    def teardown_class(cls):
        """
        1. stop ckb node
        2. clean ckb node  tmp dir
        Returns:

        """
        print("\nTeardown TestClass1")
        cls.node.stop()
        cls.node.clean()

    def setup_method(self, method):
        """
        1. clear tx pool setup for testcases
        Args:
            method:

        Returns:

        """
        self.node.getClient().clear_tx_pool()

    @pytest.mark.skip("wait for 120-rc3 release")
    def test_4698(self):
        """
        1. RPC send_transaction should not include stack trace in the RPC response
        Returns:

        """
        account = self.Ckb_cli.util_key_info_by_private_key(
            self.Config.ACCOUNT_PRIVATE_1
        )
        father_tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(
            self.Config.ACCOUNT_PRIVATE_1,
            account["address"]["testnet"],
            100000,
            self.node.getClient().url,
            "1500000",
        )

        tx = self.Tx.build_send_transfer_self_tx_with_input(
            [father_tx_hash],
            ["0x0"],
            self.Config.ACCOUNT_PRIVATE_1,
            output_count=15,
            fee=15000,
            api_url=self.node.getClient().url,
        )
        tx_hash = self.node.getClient().send_transaction(tx)
        # 1. remove tx from tx pool
        self.node.getClient().remove_transaction(tx_hash)
        tx["witnesses"][0] = "0x00"
        with pytest.raises(Exception) as exc_info:
            tx_hash = self.node.getClient().send_transaction(tx)
        # 2. use error witness check transaction can not send success,and RPC send_transaction should not include stack trace in the RPC response
        expected_error_message = "Stack backtrace"
        assert (
            expected_error_message not in exc_info.value.args[0]
        ), f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"
