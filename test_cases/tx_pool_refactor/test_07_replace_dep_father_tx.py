import time

import pytest

from framework.basic import CkbTest
from framework.util import run_command


class TestDepTx(CkbTest):

    @classmethod
    def setup_class(cls):
        cls.node1 = cls.CkbNode.init_dev_by_port(cls.CkbNodeConfigPath.CURRENT_TEST, "node/node1", 8114, 8115)
        cls.node2 = cls.CkbNode.init_dev_by_port(cls.CkbNodeConfigPath.CURRENT_TEST, "node/node2", 8116, 8117)

        cls.node1.prepare()
        cls.node1.start()
        cls.node2.prepare()
        cls.node2.start()
        cls.node2.connected(cls.node1)
        cls.Miner.make_tip_height_number(cls.node1, 300)
        cls.Node.wait_node_height(cls.node2, 300, 300)

    @classmethod
    def teardown_class(cls):
        cls.node1.stop()
        cls.node1.clean()
        cls.node2.stop()
        cls.node2.clean()

    def test_01_send_sub_transaction_replace_dep_fail(self):
        """
        发送一笔子交易，dep 的cell 为会被替换的子交易，替换失败
        1. 发送一笔父交易
        2. 发送一笔子交易
        3. 发送另外一笔子交易，dep 为会被替换的子交易
            发送失败
            Exception: Send transaction error: jsonrpc error: `Server error: PoolRejectedRBF: RBF rejected: new Tx contains cell deps from conflicts`

        """
        # 发送一笔交易
        account = self.Ckb_cli.util_key_info_by_private_key(self.Config.ACCOUNT_PRIVATE_1)
        account_private = self.Config.ACCOUNT_PRIVATE_1
        tx1_hash = self.Ckb_cli.wallet_transfer_by_private_key(account_private,
                                                               account["address"]["testnet"], 1000000,
                                                               self.node1.getClient().url, "1500000")

        # 发送一笔子交易
        tx_hash = self.Tx.send_transfer_self_tx_with_input([tx1_hash], ["0x0"], account_private,
                                                           output_count=2,
                                                           fee=1090,
                                                           api_url=self.node1.getClient().url)

        # 发送另外一笔子交易，dep 为会被替换的子交易
        with pytest.raises(Exception) as exc_info:
            self.Tx.send_transfer_self_tx_with_input([tx1_hash], ["0x0"], account_private,
                                                     output_count=2,
                                                     fee=20900,
                                                     api_url=self.node1.getClient().url,
                                                     dep_cells=[{
                                                         "tx_hash": tx_hash, "index_hex": "0x0"
                                                     }]
                                                     )

        expected_error_message = "new Tx contains cell deps from conflicts"
        assert expected_error_message in exc_info.value.args[0], \
            f"Expected substring '{expected_error_message}' " \
            f"not found in actual string '{exc_info.value.args[0]}'"
        self.node1.getClient().clear_tx_pool()

    def test_send_child_transaction_with_unreplaced_dep(self):
        """
        Test case to send a child transaction with an unspent cell (dep) and successfully replace it

        1. Send 2 transactions: tx1 and tx2
            send successful
        2. Send a child transaction: tx11
            send successful
        3. Send a transaction with dep.cell = tx2.output and replace child transaction tx11
            send successful
        4. query tx11 status
            return rejected
        """
        # 1. Send 2 transactions: tx1 and tx2
        account = self.Ckb_cli.util_key_info_by_private_key(self.Config.ACCOUNT_PRIVATE_1)
        account_private = self.Config.ACCOUNT_PRIVATE_1
        tx1_hash = self.Ckb_cli.wallet_transfer_by_private_key(account_private,
                                                               account["address"]["testnet"], 1000000,
                                                               self.node1.getClient().url, "1500000")

        account2 = self.Ckb_cli.util_key_info_by_private_key(self.Config.ACCOUNT_PRIVATE_2)
        account_private2 = self.Config.ACCOUNT_PRIVATE_2
        tx2_hash = self.Ckb_cli.wallet_transfer_by_private_key(account_private2,
                                                               account2["address"]["testnet"], 1000000,
                                                               self.node1.getClient().url, "1500000")

        # 2. Send a child transaction: tx11
        tx_hash = self.Tx.send_transfer_self_tx_with_input([tx1_hash], ["0x0"], account_private,
                                                           output_count=2,
                                                           fee=1090,
                                                           api_url=self.node1.getClient().url)

        # 3. Send a transaction with dep.cell = tx2.output and replace child transaction tx11
        replace_hash = self.Tx.send_transfer_self_tx_with_input([tx1_hash], ["0x0"], account_private,
                                                                output_count=2,
                                                                fee=20900,
                                                                api_url=self.node1.getClient().url,
                                                                dep_cells=[{
                                                                    "tx_hash": tx2_hash, "index_hex": "0x0"
                                                                }]
                                                                )

        # 4. query tx11 status
        result = self.node1.getClient().get_transaction(tx_hash)
        assert result['tx_status']['status'] == "rejected"
        self.Miner.miner_until_tx_committed(self.node1, replace_hash, True)

    def test_conflicting_sub_transaction(self):
        """
        Send another sub transaction where dep and input are the same, and there is a conflicting transaction with the pool,

            1. Send a transaction: tx1
                send successful
            2. Send a sub transaction: tx11
                send successful
            3. Send another sub transaction, dep = tx1.output, input = tx1.output ,will replace tx11
                replace successful
            4. query  tx11 status
                tx11.status == rejected
        """
        # 1. Send a transaction: tx1
        account = self.Ckb_cli.util_key_info_by_private_key(self.Config.ACCOUNT_PRIVATE_1)
        account_private = self.Config.ACCOUNT_PRIVATE_1
        tx1_hash = self.Ckb_cli.wallet_transfer_by_private_key(account_private,
                                                               account["address"]["testnet"], 1000000,
                                                               self.node1.getClient().url, "1500000")

        # 2. Send a sub transaction: tx11
        tx_hash = self.Tx.send_transfer_self_tx_with_input([tx1_hash], ["0x0"], account_private,
                                                           output_count=2,
                                                           fee=1090,
                                                           api_url=self.node1.getClient().url)

        # 3. Send another sub transaction, dep = tx1.output, input = tx1.output
        replace_hash = self.Tx.send_transfer_self_tx_with_input([tx1_hash], ["0x0"], account_private,
                                                                output_count=2,
                                                                fee=20900,
                                                                api_url=self.node1.getClient().url,
                                                                dep_cells=[{
                                                                    "tx_hash": tx1_hash, "index_hex": "0x0"
                                                                }]
                                                                )

        result = self.node1.getClient().get_transaction(tx_hash)
        assert result['tx_status']['status'] == "rejected"
        self.Miner.miner_until_tx_committed(self.node1, replace_hash, True)

    def test_replacing_sub_tx_rejects_dependent_txs(self):
        """
        When a sub transaction is replaced, other transactions in the pool referencing
        the output of the sub transaction as dep will also be rejected.

            1. Send 2 transactions: tx1, tx2

            2. Send a sub transaction: tx11

            3. Send a transaction: tx21 (dep = tx11.output)

            4. Send a transaction: will replace the previous tx11

            5. Query pool: the previous tx11 and tx21 will be rejected
        """

        #  Send 2 transactions: tx1, tx2
        account = self.Ckb_cli.util_key_info_by_private_key(self.Config.ACCOUNT_PRIVATE_1)
        account_private = self.Config.ACCOUNT_PRIVATE_1
        tx1_hash = self.Ckb_cli.wallet_transfer_by_private_key(account_private,
                                                               account["address"]["testnet"], 1000000,
                                                               self.node1.getClient().url, "1500000")

        account2 = self.Ckb_cli.util_key_info_by_private_key(self.Config.ACCOUNT_PRIVATE_2)
        account_private2 = self.Config.ACCOUNT_PRIVATE_2
        tx2_hash = self.Ckb_cli.wallet_transfer_by_private_key(account_private2,
                                                               account2["address"]["testnet"], 1000000,
                                                               self.node1.getClient().url, "1500000")

        # Send a sub transaction: tx11
        tx_hash = self.Tx.send_transfer_self_tx_with_input([tx1_hash], ["0x0"], account_private,
                                                           output_count=2,
                                                           fee=1090,
                                                           api_url=self.node1.getClient().url)

        # Send a transaction: tx21 (dep = tx11.output)
        dep_is_tx_hash = self.Tx.send_transfer_self_tx_with_input([tx2_hash], ["0x0"], account_private2,
                                                                  output_count=2,
                                                                  fee=20900,
                                                                  api_url=self.node1.getClient().url,
                                                                  dep_cells=[{
                                                                      "tx_hash": tx_hash, "index_hex": "0x0"
                                                                  }]
                                                                  )

        # Send a transaction: will replace the previous tx11
        replace_hash = self.Tx.send_transfer_self_tx_with_input([tx1_hash], ["0x0"], account_private,
                                                                output_count=2,
                                                                fee=20900,
                                                                api_url=self.node1.getClient().url,
                                                                dep_cells=[{
                                                                    "tx_hash": tx1_hash, "index_hex": "0x0"
                                                                }]
                                                                )

        # Query pool: the previous tx11 and tx21 will be rejected

        result = self.node1.getClient().get_transaction(tx_hash)
        assert result['tx_status']['status'] == "rejected"
        result = self.node1.getClient().get_transaction(dep_is_tx_hash)
        assert result['tx_status']['status'] == "rejected"
        self.Miner.miner_until_tx_committed(self.node1, replace_hash, True)
        result = self.node1.getClient().get_transaction(tx2_hash)
        assert result['tx_status']['status'] == 'committed'

    def test_tx_with_pool_dep_cell_as_input_mines_successfully(self):
        """
        Send a transaction where the input is a dep cell from another transaction in the pool -> send succeeds

            1. Send 2 transactions: tx1, tx2

            2. Send a sub transaction: tx11

            3. Send tx111, dep = tx2.output

            4. Send tx21, which will use up tx2.output

            5. Query if tx111 was mined successfully
        """
        # 1. Send 2 transactions: tx1, tx2
        account = self.Ckb_cli.util_key_info_by_private_key(self.Config.ACCOUNT_PRIVATE_1)
        account_private = self.Config.ACCOUNT_PRIVATE_1
        tx1_hash = self.Ckb_cli.wallet_transfer_by_private_key(account_private,
                                                               account["address"]["testnet"], 1000000,
                                                               self.node1.getClient().url, "1500000")

        account2 = self.Ckb_cli.util_key_info_by_private_key(self.Config.ACCOUNT_PRIVATE_2)
        account_private2 = self.Config.ACCOUNT_PRIVATE_2
        tx2_hash = self.Ckb_cli.wallet_transfer_by_private_key(account_private2,
                                                               account2["address"]["testnet"], 1000000,
                                                               self.node1.getClient().url, "1500000")

        # 2. Send a sub transaction: tx11
        tx_hash = self.Tx.send_transfer_self_tx_with_input([tx1_hash], ["0x0"], account_private,
                                                           output_count=2,
                                                           fee=1090,
                                                           api_url=self.node1.getClient().url)

        # 3. Send tx111, dep = tx2.output

        dep_cell_hash = self.Tx.send_transfer_self_tx_with_input([tx_hash], ["0x0"], account_private,
                                                                 output_count=2,
                                                                 fee=1090,
                                                                 api_url=self.node1.getClient().url,
                                                                 dep_cells=[{
                                                                     "tx_hash": tx2_hash, "index_hex": "0x0"
                                                                 }])

        # Send tx21, which will use up tx2.output
        input_cell_hash = self.Tx.send_transfer_self_tx_with_input([tx2_hash], ["0x0"], account_private2,
                                                                   output_count=2,
                                                                   fee=1090,
                                                                   api_url=self.node1.getClient().url)

        # Query if tx111 was mined successfully
        self.Miner.miner_until_tx_committed(self.node1, input_cell_hash, True)
        self.Miner.miner_until_tx_committed(self.node1, dep_cell_hash, True)

    def test_tx_with_spent_dep_cell_from_pool_fails(self):
        """
        Send a transaction where the dep cell has been spent by another transaction in the pool -> send fails

            1. Send 2 transactions: tx1, tx2

            2. Send a sub transaction: tx11

            3. Send tx21, which will use up tx2.output

            4. Send tx111, dep = tx2.output
                return error
        """
        # 1. Send 2 transactions: tx1, tx2

        account = self.Ckb_cli.util_key_info_by_private_key(self.Config.ACCOUNT_PRIVATE_1)
        account_private = self.Config.ACCOUNT_PRIVATE_1
        tx1_hash = self.Ckb_cli.wallet_transfer_by_private_key(account_private,
                                                               account["address"]["testnet"], 1000000,
                                                               self.node1.getClient().url, "1500000")

        account2 = self.Ckb_cli.util_key_info_by_private_key(self.Config.ACCOUNT_PRIVATE_2)
        account_private2 = self.Config.ACCOUNT_PRIVATE_2
        tx2_hash = self.Ckb_cli.wallet_transfer_by_private_key(account_private2,
                                                               account2["address"]["testnet"], 1000000,
                                                               self.node1.getClient().url, "1500000")

        # 2. Send a sub transaction: tx11
        tx_hash = self.Tx.send_transfer_self_tx_with_input([tx1_hash], ["0x0"], account_private,
                                                           output_count=2,
                                                           fee=1090,
                                                           api_url=self.node1.getClient().url)

        # 3. Send tx21, which will use up tx2.output
        input_cell_hash = self.Tx.send_transfer_self_tx_with_input([tx2_hash], ["0x0"], account_private2,
                                                                   output_count=2,
                                                                   fee=1090,
                                                                   api_url=self.node1.getClient().url)

        # 4. Send tx111, dep = tx2.output

        with pytest.raises(Exception) as exc_info:
            self.Tx.send_transfer_self_tx_with_input([tx_hash], ["0x0"], account_private,
                                                     output_count=2,
                                                     fee=1090,
                                                     api_url=self.node1.getClient().url,
                                                     dep_cells=[{
                                                         "tx_hash": tx2_hash, "index_hex": "0x0"
                                                     }])
        expected_error_message = "TransactionFailedToResolve"
        assert expected_error_message in exc_info.value.args[0], \
            f"Expected substring '{expected_error_message}' " \
            f"not found in actual string '{exc_info.value.args[0]}'"
        self.node1.getClient().clear_tx_pool()

    def test_sync_order_for_tx_with_pool_cell_dependency(self):
        """
        The node receives the depCell transaction first, then receives the transaction consuming the depCell.
        When relaying the transactions to another node, it relays the transaction consuming the depCell first,
        then relays the depCell transaction.

        1. Send 2 transactions: tx1, tx2
        2. Send a sub transaction: tx11
        3. Miner mines
        4. Send dep cell = tx2.output[0]
        5. Send tx21
        6. Delete node2 data, resync node2
        7. Ensure node2 pool is empty
        8. Resend tx21 to node1 first to sync to node2
        9. Resend `dep cell transaction` that dep cell = tx2.output[0]
        10. Query for `dep cell transaction` on node2 and node1
            node1: pending
            node2: rejected
        """
        # 1. Send 2 transactions: tx1, tx2

        account = self.Ckb_cli.util_key_info_by_private_key(self.Config.ACCOUNT_PRIVATE_1)
        account_private = self.Config.ACCOUNT_PRIVATE_1
        tx1_hash = self.Ckb_cli.wallet_transfer_by_private_key(account_private,
                                                               account["address"]["testnet"], 1000000,
                                                               self.node1.getClient().url, "1500000")

        account2 = self.Ckb_cli.util_key_info_by_private_key(self.Config.ACCOUNT_PRIVATE_2)
        account_private2 = self.Config.ACCOUNT_PRIVATE_2
        tx2_hash = self.Ckb_cli.wallet_transfer_by_private_key(account_private2,
                                                               account2["address"]["testnet"], 1000000,
                                                               self.node1.getClient().url, "1500000")

        # 2. Send a sub transaction: tx11
        tx_hash = self.Tx.send_transfer_self_tx_with_input([tx1_hash], ["0x0"], account_private,
                                                           output_count=2,
                                                           fee=1090,
                                                           api_url=self.node1.getClient().url)
        # 3. Miner mines
        self.Miner.miner_until_tx_committed(self.node1, tx_hash, True)
        self.Miner.miner_until_tx_committed(self.node1, tx2_hash, True)

        # 4. Send dep cell = tx2.output[0]

        dep_cell_hash = self.Tx.send_transfer_self_tx_with_input([tx_hash], ["0x0"], account_private,
                                                                 output_count=2,
                                                                 fee=1090,
                                                                 api_url=self.node1.getClient().url,
                                                                 dep_cells=[{
                                                                     "tx_hash": tx2_hash, "index_hex": "0x0"
                                                                 }])

        # 5. Send tx21
        input_cell_hash = self.Tx.send_transfer_self_tx_with_input([tx2_hash], ["0x0"], account_private2,
                                                                   output_count=2,
                                                                   fee=1090,
                                                                   api_url=self.node1.getClient().url)

        time.sleep(5)

        #  6. Delete node2 data, resync node2
        self.node2.restart(clean_data=True)

        self.node2.connected(self.node1)
        tip_number = self.node1.getClient().get_tip_block_number()
        self.Node.wait_node_height(self.node2, tip_number, 300)
        time.sleep(10)

        # 7. Ensure node2 pool is empty
        node2_pool = self.node2.getClient().tx_pool_info()
        assert node2_pool['pending'] == '0x0'

        # 8. Resend tx21 to node1 first to sync to node2
        tx1 = self.node1.getClient().get_transaction(input_cell_hash)
        del tx1['transaction']['hash']
        try:
            self.node2.getClient().send_transaction(tx1['transaction'])
            time.sleep(1)
            result = self.node2.getClient().get_raw_tx_pool()
            assert tx1 in result['pending']
            assert len(result['pending']) == 1
        except Exception:
            pass

        # 9. Resend `dep cell transaction` that dep cell = tx2.output[0]
        tx1 = self.node1.getClient().get_transaction(dep_cell_hash)
        del tx1['transaction']['hash']
        try:
            self.node2.getClient().send_transaction(tx1['transaction'])
            time.sleep(1)
        except Exception:
            pass

        # 10. Query for `dep cell transaction` on node2
        self.node1.getClient().tx_pool_info()
        self.node2.getClient().tx_pool_info()
        self.node1.getClient().get_transaction(dep_cell_hash)
        result = self.node2.getClient().get_transaction(dep_cell_hash)
        assert result['tx_status']['status'] == 'rejected'
