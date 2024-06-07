import pytest

from framework.basic import CkbTest


class TxpoolMaxAncestorsCount(CkbTest):
    @classmethod
    def setup_class(cls):
        cls.node = cls.CkbNode.init_dev_by_port(
            cls.CkbNodeConfigPath.CURRENT_TEST, "tx_pool/node1", 8120, 8225
        )
        cls.node.prepare(
            other_ckb_config={"ckb_tx_pool_max_ancestors_count": "180_000"}
        )
        cls.node.prepare()
        cls.node.start()
        cls.Miner.make_tip_height_number(cls.node, 30)

    @classmethod
    def teardown_class(cls):
        cls.node.stop()
        cls.node.clean()

    @pytest.mark.skip
    def test_very_max_ancestors_count(self):
        """
        test very big ancestors_count
        1. build tx1
        2. send linked tx use tx1
        Returns:

        """
        # 1. build tx1
        account = self.Ckb_cli.util_key_info_by_private_key(
            self.Config.ACCOUNT_PRIVATE_1
        )
        tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(
            self.Config.ACCOUNT_PRIVATE_1,
            account["address"]["testnet"],
            10000,
            self.node.getClient().url,
            "1500",
        )
        # 2. send linked tx use tx1
        for i in range(170_000):
            pool_info = self.node.getClient().tx_pool_info()
            print(pool_info)
            tx_pool = self.node.getClient().get_raw_tx_pool(True)
            print("tx_pool:", tx_pool)
            print("current i:", i)
            tx_hash = self.Tx.send_transfer_self_tx_with_input(
                [tx_hash],
                ["0x0"],
                self.Config.ACCOUNT_PRIVATE_1,
                fee=1000,
                output_count=1,
                api_url=self.node.getClient().url,
            )
