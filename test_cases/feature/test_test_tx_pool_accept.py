import pytest

from framework.basic import CkbTest


class TestTestTxPoolAccept(CkbTest):

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

    def test_normal_tx(self):
        """
        1. generate account and build normal tx
        2. send the normal tx ,use the tx hash by test_tx_pool_accept check
        3. assert transactions in tx pool with fee and cycles
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

    def test_min_fee_rejected(self):
        """
        1. generate account and build normal tx
        2. send the normal tx ,but fee is PoolRejectedTransactionByMinFeeRate use the tx hash by test_tx_pool_accept check
        3. assert PoolRejectedTransactionByMinFeeRate
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
        # 2. send the normal tx ,but fee is PoolRejectedTransactionByMinFeeRate use the tx hash by test_tx_pool_accept check
        tx = self.Tx.build_send_transfer_self_tx_with_input(
            [father_tx_hash],
            ["0x0"],
            self.Config.ACCOUNT_PRIVATE_1,
            output_count=15,
            fee=15,
            api_url=self.node.getClient().url,
        )

        with pytest.raises(Exception) as exc_info:
            response = self.node.getClient().test_tx_pool_accept(tx, "passthrough")
        expected_error_message = "PoolRejectedTransactionByMinFeeRate"
        print("exc_info.value.args[0]:", exc_info.value.args[0])
        # 3. assert PoolRejectedTransactionByMinFeeRate
        assert (
            expected_error_message in exc_info.value.args[0]
        ), f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

    def test_err_outputs_validator(self):
        """
        1. generate account and build normal tx
        2. use the tx hash by test_tx_pool_accept by Invalid parameter for `outputs_validator check
        3. assert Invalid parameter for `outputs_validator
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
        # 2. use the tx hash by test_tx_pool_accept by Invalid parameter for `outputs_validator check
        with pytest.raises(Exception) as exc_info:
            response = self.node.getClient().test_tx_pool_accept(tx, "other")

        expected_error_message = "Invalid parameter for `outputs_validator`"
        print("exc_info.value.args[0]:", exc_info.value.args[0])
        # 3. assert Invalid parameter for `outputs_validator
        assert (
            expected_error_message in exc_info.value.args[0]
        ), f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

    def test_dup_cell_tx(self):
        """
        1. generate account and build normal tx
        2. send tx twice and  test_tx_pool_accept by PoolRejectedDuplicatedTransaction check
        3. assert PoolRejectedDuplicatedTransaction
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
        # 2. send tx twice and  test_tx_pool_accept by PoolRejectedDuplicatedTransaction check
        self.node.getClient().send_transaction(tx)
        with pytest.raises(Exception) as exc_info:
            response = self.node.getClient().test_tx_pool_accept(tx, "passthrough")

        expected_error_message = "PoolRejectedDuplicatedTransaction"
        print("exc_info.value.args[0]:", exc_info.value.args[0])
        # 3. assert PoolRejectedDuplicatedTransaction
        assert (
            expected_error_message in exc_info.value.args[0]
        ), f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

    def test_send_link_tx(self):
        """
        1. generate account and build normal tx
        2. send link tx and test_tx_pool_accept check success
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
        tx_hash = father_tx_hash
        # 2. send link tx and test_tx_pool_accept check success
        for i in range(3):
            tx = self.Tx.build_send_transfer_self_tx_with_input(
                [tx_hash],
                [hex(0)],
                self.Config.ACCOUNT_PRIVATE_1,
                output_count=1,
                fee=1100090 + i * 1000,
                api_url=self.node.getClient().url,
            )
            test_tx_pool_accept_response = self.node.getClient().test_tx_pool_accept(
                tx, "passthrough"
            )
            tx_hash = self.node.getClient().send_transaction(tx)

    @pytest.mark.skip
    def test_pool_full(self):
        """
        1. generate account and build normal tx
        2. tx pool is full and test_tx_pool_accept check success
        Returns:

        """
        account = self.Ckb_cli.util_key_info_by_private_key(
            self.Config.ACCOUNT_PRIVATE_1
        )
        father_tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(
            self.Config.ACCOUNT_PRIVATE_1,
            account["address"]["testnet"],
            1500000,
            self.node.getClient().url,
            "1500000",
        )
        tx_hash = father_tx_hash
        send_tx_list = []
        for i in range(10):
            print("current idx:", i)
            tx = self.Tx.build_send_transfer_self_tx_with_input(
                [tx_hash],
                [hex(0)],
                self.Config.ACCOUNT_PRIVATE_1,
                output_count=1,
                fee=1000000 - i * 1000,
                api_url=self.node.getClient().url,
            )
            response = self.node.getClient().test_tx_pool_accept(tx, "passthrough")

            tx_hash = self.node.getClient().send_transaction(tx)
            send_tx_list.append(tx_hash)

        with pytest.raises(Exception) as exc_info:
            tx = self.Tx.build_send_transfer_self_tx_with_input(
                [tx_hash],
                [hex(0)],
                self.Config.ACCOUNT_PRIVATE_1,
                output_count=1,
                fee=1000000 - i * 1000,
                api_url=self.node.getClient().url,
            )
            response = self.node.getClient().test_tx_pool_accept(tx, "passthrough")
        expected_error_message = "PoolIsFull"
        assert (
            expected_error_message in exc_info.value.args[0]
        ), f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"
        with pytest.raises(Exception) as exc_info:
            self.node.getClient().send_transaction(tx)

    def test_TransactionFailedToVerify(self):
        """
        1. generate account and build normal tx
        2. use error witness add tx build so test_tx_pool_accept check failed TransactionFailedToVerify
        3. assert TransactionFailedToVerify by test_tx_pool_accept
        Returns:

        """
        # 1. generate account and build normal tx
        account = self.Ckb_cli.util_key_info_by_private_key(
            self.Config.ACCOUNT_PRIVATE_1
        )
        father_tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(
            self.Config.ACCOUNT_PRIVATE_1,
            account["address"]["testnet"],
            1500000,
            self.node.getClient().url,
            "1500000",
        )
        print(f"father_tx_hash:", father_tx_hash)
        tx_hash = father_tx_hash
        send_tx_list = []
        for i in range(10):
            print("current idx:", i)
            tx = self.Tx.build_send_transfer_self_tx_with_input(
                [tx_hash],
                [hex(0)],
                self.Config.ACCOUNT_PRIVATE_1,
                output_count=1,
                fee=1000000 - i * 1000,
                api_url=self.node.getClient().url,
            )
            response = self.node.getClient().test_tx_pool_accept(tx, "passthrough")

            tx_hash = self.node.getClient().send_transaction(tx)
            send_tx_list.append(tx_hash)

        with pytest.raises(Exception) as exc_info:
            # 2. use error witness add tx build so test_tx_pool_accept check failed TransactionFailedToVerify
            tx = self.Tx.build_send_transfer_self_tx_with_input_err(
                [tx_hash],
                [hex(0)],
                self.Config.ACCOUNT_PRIVATE_1,
                output_count=1,
                fee=1000000 - i * 1000,
                api_url=self.node.getClient().url,
            )
            response = self.node.getClient().test_tx_pool_accept(tx, "passthrough")
            # 3. assert TransactionFailedToVerify by test_tx_pool_accept
            expected_error_message = "TransactionFailedToVerify"
            assert (
                expected_error_message in exc_info.value.args[0]
            ), f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"
            with pytest.raises(Exception) as exc_info:
                self.node.getClient().send_transaction(tx)

    def test_TransactionFailedToResolve(self):
        """
        1. generate account and build normal tx
        2. use error cell dep add tx build so test_tx_pool_accept check failed TransactionFailedToResolve
        3. assert TransactionFailedToResolve by test_tx_pool_accept
        Returns:

        """
        # 1. generate account and build normal tx
        account = self.Ckb_cli.util_key_info_by_private_key(
            self.Config.ACCOUNT_PRIVATE_1
        )
        father_tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(
            self.Config.ACCOUNT_PRIVATE_1,
            account["address"]["testnet"],
            1500000,
            self.node.getClient().url,
            "1500000",
        )
        print(f"father_tx_hash:", father_tx_hash)
        tx_hash = father_tx_hash
        send_tx_list = []
        for i in range(10):
            print("current idx:", i)
            tx = self.Tx.build_send_transfer_self_tx_with_input(
                [tx_hash],
                [hex(0)],
                self.Config.ACCOUNT_PRIVATE_1,
                output_count=1,
                fee=1000000 - i * 1000,
                api_url=self.node.getClient().url,
            )
            response = self.node.getClient().test_tx_pool_accept(tx, "passthrough")

            tx_hash = self.node.getClient().send_transaction(tx)
            send_tx_list.append(tx_hash)

        with pytest.raises(Exception) as exc_info:
            # 2. use error cell dep add tx build so test_tx_pool_accept check failed TransactionFailedToResolve
            tx = self.Tx.build_send_transfer_self_tx_with_input_err2(
                [tx_hash],
                [hex(0)],
                self.Config.ACCOUNT_PRIVATE_1,
                output_count=1,
                fee=1000000 - i * 1000,
                api_url=self.node.getClient().url,
            )
            response = self.node.getClient().test_tx_pool_accept(tx, "passthrough")
            # 3. assert TransactionFailedToResolve by test_tx_pool_accept
        expected_error_message = "TransactionFailedToResolve"
        assert (
            expected_error_message in exc_info.value.args[0]
        ), f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"
        with pytest.raises(Exception) as exc_info:
            self.node.getClient().send_transaction(tx)

    def test_change_cache_tx(self):
        """
        1. remove tx from tx pool
        2. use error witness check transaction can not send success
        3. assert ValidationFailure
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
            # 2. use error witness check transaction can not send success
        expected_error_message = "ValidationFailure"
        assert (
            expected_error_message in exc_info.value.args[0]
        ), f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"
        with pytest.raises(Exception) as exc_info:
            tx_hash = self.node.getClient().test_tx_pool_accept(tx, "passthrough")
        expected_error_message = "ValidationFailure"
        # 3. assert ValidationFailure
        assert (
            expected_error_message in exc_info.value.args[0]
        ), f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"
