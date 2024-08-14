from framework.basic import CkbTest
import pytest


class TestGetTransaction(CkbTest):

    @classmethod
    def setup_class(cls):
        """
        1. start 1 ckb node in tmp/get_transaction/node1 node dir
        2. miner 100block
        Returns:

        """
        # 1. start 1 ckb node in tmp/get_transaction/node1 node dir
        cls.node = cls.CkbNode.init_dev_by_port(
            cls.CkbNodeConfigPath.develop, "get_transaction/node1", 8120, 8225
        )
        cls.node.prepare(other_ckb_config={"ckb_tx_pool_max_tx_pool_size": "180_000"})
        cls.node.start()
        # 2. miner 100 block
        cls.Miner.make_tip_height_number(cls.node, 100)

    @classmethod
    def teardown_class(cls):
        """
        1. stop ckb node
        2. clean ckb node  tmp dir
        Returns:

        """
        cls.node.stop()
        cls.node.clean()

    # @pytest.mark.skip("util v118 rc")
    def test_get_transaction_by_tx_index(self):
        """
        1. new tx in block
        2. query tx index is null
        3. miner block until tx committed， query tx index is 0x1
        Returns:

        """
        # 1. new tx in block
        account = self.Ckb_cli.util_key_info_by_private_key(self.Config.MINER_PRIVATE_1)
        tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(
            self.Config.MINER_PRIVATE_1,
            account["address"]["testnet"],
            100,
            self.node.getClient().url,
            "1500",
        )
        print(f"txHash:{tx_hash}")
        # 2. query tx index is null
        transaction1 = self.node.getClient().get_transaction(tx_hash)
        print(f"tx_index:{transaction1['tx_status']['tx_index']}")
        assert transaction1["tx_status"]["tx_index"] is None
        # 3. miner block until tx committed， query tx index is 0x1
        self.Miner.miner_until_tx_committed(self.node, tx_hash)
        transaction2 = self.node.getClient().get_transaction(tx_hash)
        print(f"after miner tx_hash, tx_index:{transaction2['tx_status']['tx_index']}")
        assert transaction2["tx_status"]["tx_index"] == "0x1"
