import pytest
from framework.basic import CkbTest


class TestSendTxWhenPoolLimit(CkbTest):
    @classmethod
    def setup_class(cls):
        cls.node = cls.CkbNode.init_dev_by_port(cls.CkbNodeConfigPath.CURRENT_TEST, "tx_pool/node1", 8120,
                                                8225)
        cls.node.prepare(other_ckb_config={"ckb_tx_pool_max_tx_pool_size": "4640"})
        cls.node.start()
        cls.Miner.make_tip_height_number(cls.node, 30)

    def setup_method(self, method):
        """
        clean tx pool
        :param method:
        :return:
        """
        # self.node.getClient().clear_tx_pool()
        for i in range(5):
            self.Miner.miner_with_version(self.node, "0x0")
        pool = self.node.getClient().tx_pool_info()
        print("pool:", pool)

    @classmethod
    def teardown_class(cls):
        cls.node.stop()
        cls.node.clean()

    def test_replace_same_father_link_tx_when_tx_pool_full(self):
        """
        能够替换父交易其他output产生的子交易
        cellDep的交易手续费很低，子交易只会替换其他交易不会替换被其他高fee交易当cellDep的交易
        父交易手续费最低，子交易只会替换其他交易不会替换父交易

        Returns:

        """
        account = self.Ckb_cli.util_key_info_by_private_key(self.Config.ACCOUNT_PRIVATE_1)
        father_tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(self.Config.ACCOUNT_PRIVATE_1,
                                                                     account["address"]["testnet"], 100000,
                                                                     self.node.getClient().url, "1500000")

        tx_hash_2 = self.Ckb_cli.wallet_transfer_by_private_key(self.Config.ACCOUNT_PRIVATE_2,
                                                                account["address"]["testnet"], 100000,
                                                                self.node.getClient().url, "1000")

        tx_list = [father_tx_hash, tx_hash_2]
        tx_hash = self.Tx.send_transfer_self_tx_with_input([father_tx_hash], ['0x0'], self.Config.ACCOUNT_PRIVATE_1,
                                                           output_count=15,
                                                           fee=15000,
                                                           api_url=self.node.getClient().url)
        tx_list.append(tx_hash)
        for i in range(0, 15):
            print("current i:", i)
            tx_hash1 = self.Tx.send_transfer_self_tx_with_input([tx_hash], [hex(i)], self.Config.ACCOUNT_PRIVATE_1,
                                                                output_count=1,
                                                                fee=10000 * 2 ** i,
                                                                dep_cells=[{"tx_hash": tx_hash_2, "index_hex": "0x0"}],
                                                                api_url=self.node.getClient().url)
            tx_list.append(tx_hash1)
        response = self.node.getClient().get_transaction(tx_hash_2)
        assert response['tx_status']['status'] != "unknown"
        response = self.node.getClient().get_transaction(father_tx_hash)
        assert response['tx_status']['status'] != "unknown"
        unknown = 0
        for tx_hash in tx_list:
            response = self.node.getClient().get_transaction(tx_hash)
            print(response)
            if response['tx_status']['status'] == "unknown":
                unknown += 1
        assert unknown == 11

    def test_replace_normal_tx_when_tx_pool_full(self):
        """
        交易池都是普通交易, 交易池满时，发送一笔手续费比较高的交易，发送成功，手续费比较低的交易会被移除

        1. send 10 normal tx
        2. send 12 tx that  fee > 10 normal tx
        3. 12 tx status == pending
        4. 8 normal tx status == unknown
        Returns:

        """
        account = self.Ckb_cli.util_key_info_by_private_key(self.Config.ACCOUNT_PRIVATE_1)
        tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(self.Config.ACCOUNT_PRIVATE_1,
                                                              account["address"]["testnet"], 1000000,
                                                              self.node.getClient().url, "1500000")
        tx_hash = self.Tx.send_transfer_self_tx_with_input([tx_hash], ['0x0'], self.Config.ACCOUNT_PRIVATE_1,
                                                           output_count=10,
                                                           fee=1500000,
                                                           api_url=self.node.getClient().url)
        self.Miner.miner_until_tx_committed(self.node, tx_hash)
        tx_list = []
        for i in range(0, 10):
            print("current i:", i)
            tx_hash1 = self.Tx.send_transfer_self_tx_with_input([tx_hash], [hex(i)], self.Config.ACCOUNT_PRIVATE_1,
                                                                output_count=1,
                                                                fee=1090 + i,
                                                                api_url=self.node.getClient().url)
            tx_list.append(tx_hash1)

        tx_hash_a = tx_hash
        tx_hash_a_list = []
        for i in range(12):
            print("tx_hash_a_list current i:", i)
            tx_hash_a = self.Tx.send_transfer_self_tx_with_input([tx_hash_a], [hex(0)], self.Config.ACCOUNT_PRIVATE_1,
                                                                 output_count=1,
                                                                 fee=11090 + i * 1000,
                                                                 api_url=self.node.getClient().url)
            tx_hash_a_list.append(tx_hash_a)
        unknown_status_size = 0
        for tx_hash in tx_list:
            tx = self.node.getClient().get_transaction(tx_hash)
            if tx['tx_status']['status'] == "unknown":
                unknown_status_size += 1
        for tx_hash_a in tx_hash_a_list:
            tx = self.node.getClient().get_transaction(tx_hash_a)
            assert tx['tx_status']['status'] != "unknown"
        assert unknown_status_size == 8

    def test_replace_link_tx_when_ckb_tx_pool_full(self):
        """
        xxxx 交易(fee = 500000000)
        链式交易:a(fee=1000)-> b(fee=2000)- ->c(fee=3000)- -> d(fee=4000) -> e(fee=5000)
        插入tx(fee=500000),那会导致a,b,c,d,e 交易都被移除
        Returns:
        """
        account = self.Ckb_cli.util_key_info_by_private_key(self.Config.ACCOUNT_PRIVATE_1)
        tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(self.Config.ACCOUNT_PRIVATE_1,
                                                              account["address"]["testnet"], 1000000,
                                                              self.node.getClient().url, "1500000")
        tx_hash = self.Tx.send_transfer_self_tx_with_input([tx_hash], ['0x0'], self.Config.ACCOUNT_PRIVATE_1,
                                                           output_count=10,
                                                           fee=1500000,
                                                           api_url=self.node.getClient().url)
        self.Miner.miner_until_tx_committed(self.node, tx_hash)
        tx_hash_a = tx_hash
        tx_hash_a_list = []
        for i in range(12):
            print("tx_hash_a_list current i:", i)
            tx_hash_a = self.Tx.send_transfer_self_tx_with_input([tx_hash_a], [hex(0)], self.Config.ACCOUNT_PRIVATE_1,
                                                                 output_count=1,
                                                                 fee=11090 + i * 1000,
                                                                 api_url=self.node.getClient().url)
            tx_hash_a_list.append(tx_hash_a)

        tx_hash_b = tx_hash
        tx_hash_b_list = []
        tx_hash_b = self.Tx.send_transfer_self_tx_with_input([tx_hash_b], [hex(1)], self.Config.ACCOUNT_PRIVATE_1,
                                                             output_count=1,
                                                             fee=1100090 + i * 1000,
                                                             api_url=self.node.getClient().url)
        tx_hash_b_list.append(tx_hash_b)
        for i in range(3):
            print("tx_hash_b_list current i:", i)

            tx_hash_b = self.Tx.send_transfer_self_tx_with_input([tx_hash_b], [hex(0)], self.Config.ACCOUNT_PRIVATE_1,
                                                                 output_count=1,
                                                                 fee=110000000 + i * 10000000,
                                                                 api_url=self.node.getClient().url)
            tx_hash_b_list.append(tx_hash_b)
        for tx_hash_a in tx_hash_a_list:
            tx = self.node.getClient().get_transaction(tx_hash_a)
            assert tx['tx_status']['status'] == 'unknown'
        for tx_hash_b in tx_hash_b_list:
            self.node.getClient().get_transaction(tx_hash_b)

    def test_cant_replace_father_tx_when_ckb_tx_pool_full(self):
        """
        交易池全是父交易，子交易手续费给再高，都是报pool is full

        Returns:

        """
        account = self.Ckb_cli.util_key_info_by_private_key(self.Config.ACCOUNT_PRIVATE_1)
        tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(self.Config.ACCOUNT_PRIVATE_1,
                                                              account["address"]["testnet"], 1000000,
                                                              self.node.getClient().url, "1500000")
        tx_hash = self.Tx.send_transfer_self_tx_with_input([tx_hash], ['0x0'], self.Config.ACCOUNT_PRIVATE_1,
                                                           output_count=10,
                                                           fee=1500000,
                                                           api_url=self.node.getClient().url)
        self.Miner.miner_until_tx_committed(self.node, tx_hash)
        with pytest.raises(Exception) as exc_info:
            for i in range(22):
                tx_hash = self.Tx.send_transfer_self_tx_with_input([tx_hash], [hex(0)], self.Config.ACCOUNT_PRIVATE_1,
                                                                   output_count=1,
                                                                   fee=11090 + i * 1000,
                                                                   api_url=self.node.getClient().url)

        expected_error_message = "PoolIsFull"
        print("exc_info.value.args[0]:", exc_info.value.args[0])
        assert expected_error_message in exc_info.value.args[0], \
            f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"
