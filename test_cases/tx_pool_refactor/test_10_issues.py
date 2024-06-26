import pytest

from framework.basic import CkbTest


class TestIssues(CkbTest):

    @classmethod
    def setup_class(cls):
        cls.node1 = cls.CkbNode.init_dev_by_port(
            cls.CkbNodeConfigPath.CURRENT_TEST, "tx_pool/node1", 8120, 8225
        )
        cls.node1.prepare()
        cls.node1.start()
        cls.Miner.make_tip_height_number(cls.node1, 30)

    @classmethod
    def teardown_class(cls):
        cls.node1.stop()
        cls.node1.clean()

    def test_4315(self):
        """
        1. Send tx1
        2. Send tx(1000): dep(tx1.output)
        3. Send transaction consuming tx1.output
        4. Send dependent on tx1.output
        """
        # 1. Send tx1

        account = self.Ckb_cli.util_key_info_by_private_key(
            self.Config.ACCOUNT_PRIVATE_2
        )
        account_private = self.Config.ACCOUNT_PRIVATE_2
        tx1_hash = self.Ckb_cli.wallet_transfer_by_private_key(
            account_private,
            account["address"]["testnet"],
            10000000,
            self.node1.getClient().url,
            "1500000",
        )
        tx11_hash = self.Tx.send_transfer_self_tx_with_input(
            [tx1_hash],
            ["0x0"],
            account_private,
            output_count=20,
            fee=10090,
            api_url=self.node1.getClient().url,
            dep_cells={},
        )
        self.Miner.miner_until_tx_committed(self.node1, tx11_hash)
        # 2. Send tx(1000): dep(tx1.output)
        for j in range(10):
            tx_hash = self.Tx.send_transfer_self_tx_with_input(
                [tx11_hash],
                [hex(j)],
                account_private,
                output_count=1,
                fee=1090,
                api_url=self.node1.getClient().url,
                dep_cells=[{"tx_hash": tx11_hash, "index_hex": hex(19)}],
            )
            for i in range(20):
                print("curent i:", i, "curent j:", j)
                tx_hash = self.Tx.send_transfer_self_tx_with_input(
                    [tx_hash],
                    ["0x0"],
                    account_private,
                    output_count=1,
                    fee=1090,
                    api_url=self.node1.getClient().url,
                    dep_cells=[{"tx_hash": tx11_hash, "index_hex": hex(19)}],
                )

        # 3. Send transaction consuming tx1.output
        tx_hash = self.Tx.send_transfer_self_tx_with_input(
            [tx11_hash],
            [hex(19)],
            account_private,
            output_count=1,
            fee=1090000,
            api_url=self.node1.getClient().url,
            dep_cells=[],
        )
        # 4. Send dependent on tx1.output
        with pytest.raises(Exception) as exc_info:
            tx_hash = self.Tx.send_transfer_self_tx_with_input(
                [tx11_hash],
                [hex(11)],
                account_private,
                output_count=1,
                fee=1090,
                api_url=self.node1.getClient().url,
                dep_cells=[{"tx_hash": tx11_hash, "index_hex": hex(19)}],
            )
        expected_error_message = "Resolve failed Dead"
        assert expected_error_message in exc_info.value.args[0], (
            f"Expected substring '{expected_error_message}' "
            f"not found in actual string '{exc_info.value.args[0]}'"
        )

    def test_4306(self):
        """
        Old transaction chain A -> B -> C, a new transaction D is issued, but transaction D has a cell dependency on C, hence RBF (Replace-By-Fee) will not succeed.
        The previous code logic only checked whether D was cell dependent on A; it should check all descendants.
        1. Send tx1
        2. Send tx11
        3. Send tx111
        4. Send tx12(cellDep = tx111.output )
        """
        # 1. Send tx1
        account = self.Ckb_cli.util_key_info_by_private_key(
            self.Config.ACCOUNT_PRIVATE_1
        )
        account_private = self.Config.ACCOUNT_PRIVATE_1
        tx1_hash = self.Ckb_cli.wallet_transfer_by_private_key(
            account_private,
            account["address"]["testnet"],
            1000000,
            self.node1.getClient().url,
            "1500000",
        )

        # 2. Send a sub transaction: tx11
        tx11_hash = self.Tx.send_transfer_self_tx_with_input(
            [tx1_hash],
            ["0x0"],
            account_private,
            output_count=2,
            fee=1090,
            api_url=self.node1.getClient().url,
        )

        # 3. Send tx111
        tx111_hash = self.Tx.send_transfer_self_tx_with_input(
            [tx11_hash],
            ["0x0"],
            account_private,
            output_count=2,
            fee=1090,
            api_url=self.node1.getClient().url,
        )
        # 4. Send tx12(cellDep = tx111.output )
        with pytest.raises(Exception) as exc_info:

            replace_hash = self.Tx.send_transfer_self_tx_with_input(
                [tx1_hash],
                ["0x0"],
                account_private,
                output_count=2,
                fee=20900,
                api_url=self.node1.getClient().url,
                dep_cells=[{"tx_hash": tx111_hash, "index_hex": "0x1"}],
            )
        expected_error_message = (
            "RBF rejected: new Tx contains cell deps from conflicts"
        )
        assert expected_error_message in exc_info.value.args[0], (
            f"Expected substring '{expected_error_message}' "
            f"not found in actual string '{exc_info.value.args[0]}'"
        )
