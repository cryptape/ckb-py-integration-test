from framework.basic import CkbTest


class TestCleanVerifyQueueByCkbCli(CkbTest):

    @classmethod
    def setup_class(cls):
        """
        1. start 1 ckb node in tmp/feature/TestCleanVerifyQueueByCkbCli/node1 dir
        2. miner 20 block
        Returns:

        """
        cls.node = cls.CkbNode.init_dev_by_port(
            cls.CkbNodeConfigPath.CURRENT_TEST,
            "feature/TestCleanVerifyQueueByCkbCli/node1",
            8314,
            8315,
        )
        cls.node.prepare(other_ckb_config={"ckb_tx_pool_max_tx_pool_size": "4640"})
        cls.node.start()
        cls.Miner.make_tip_height_number(cls.node, 20)

    @classmethod
    def teardown_class(cls):
        """
        1. stop ckb node
        2. clean ckb node tmp dir
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

    def test_clean_verify_queue_by_ckb_cli(self):
        """
        # 1. generate account and build normal tx
        # 2. send the normal tx ,use the tx hash by test_tx_pool_accept check
        # 3. assert transactions in tx pool with fee and cycles
        # 4. get tx_pool_info
        # 5. use clean_verify_queue_by_ckb_cli and get tx_pool_info
        Returns:

        """
        # 1. generate account and build normal tx
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
        # 2. send the normal tx ,use the tx hash by test_tx_pool_accept check
        response = self.node.getClient().test_tx_pool_accept(tx, "passthrough")
        tx_hash = self.node.getClient().send_transaction(tx)
        tx_pool = self.node.getClient().get_raw_tx_pool(True)
        # 3. assert transactions in tx pool with fee and cycles
        assert tx_pool["pending"][tx_hash]["fee"] == response["fee"]
        assert tx_pool["pending"][tx_hash]["cycles"] == response["cycles"]
        # 4. get tx_pool_info
        tx_pool_info = self.node.getClient().tx_pool_info()
        print(f"tx_pool_info:{tx_pool_info}")
        # 5. use clean_verify_queue_by_ckb_cli and get tx_pool_info
        self.Ckb_cli.version()
        rep = self.Ckb_cli.clear_tx_verify_queue(api_url=self.node.getClient().url)
        tx_pool_info = self.node.getClient().tx_pool_info()
        print(f"tx_pool_info:{tx_pool_info}")
        assert tx_pool_info["verify_queue_size"] == "0x0"
