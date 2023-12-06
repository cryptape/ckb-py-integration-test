import time

from framework.basic import CkbTest
import concurrent.futures


class ManyTx(CkbTest):

    @classmethod
    def setup_class(cls):
        cls.current_node = cls.CkbNode.init_dev_by_port(cls.CkbNodeConfigPath.CURRENT_TEST, "tx_pool/node1", 8120,
                                                        8225)
        cls.node_111 = cls.CkbNode.init_dev_by_port(cls.CkbNodeConfigPath.V111, "tx_pool/node2", 8121,
                                                    8226)
        cls.cluster = cls.Cluster([cls.current_node, cls.node_111])
        cls.cluster.prepare_all_nodes()
        cls.cluster.start_all_nodes()
        cls.cluster.connected_all_nodes()
        cls.Miner.make_tip_height_number(cls.current_node, 200)
        cls.Node.wait_cluster_height(cls.cluster, 150, 50)

    @classmethod
    def teardown_class(cls):
        cls.cluster.stop_all_nodes()
        cls.cluster.clean_all_nodes()

    def test_may_tx(self):
        """
        1. 给节点1 并发发送冲突子交易
        2. 查询节点的pool池
            pending = 1
        """
        TEST_PRIVATE_1 = self.Config.MINER_PRIVATE_1

        account = self.Ckb_cli.util_key_info_by_private_key(TEST_PRIVATE_1)
        tx1 = self.Ckb_cli.wallet_transfer_by_private_key(self.Config.MINER_PRIVATE_1,
                                                          account["address"]["testnet"], 100,
                                                          self.current_node.getClient().url, "1500")
        self.Miner.miner_until_tx_committed(self.current_node, tx1)
        tip_number = self.current_node.getClient().get_tip_block_number()
        self.Node.wait_node_height(self.node_111, tip_number, 1000)
        self.node_111.getClient().set_network_active(False)

        txs = []
        # 给节点1 并发发送
        for i in range(10):
            tx = self.Tx.send_transfer_self_tx_with_input([tx1], ["0x0"], TEST_PRIVATE_1,
                                                          output_count=1,
                                                          fee=1090 + i,
                                                          api_url=self.node_111.getClient().url)
            transaction = self.node_111.getClient().get_transaction(tx)
            transaction = transaction['transaction']
            del transaction['hash']
            txs.insert(0, transaction)

        successfulSize = 0
        successfulTxHash = ""
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {executor.submit(self.current_node.getClient().send_transaction, tx): tx for tx in txs}
            for future in concurrent.futures.as_completed(futures):
                tx = futures[future]
                try:
                    result = future.result()
                    # 处理返回结果
                    print(f"Transaction sent successfully: {result}")
                    successfulSize += 1
                    successfulTxHash = result
                except Exception as e:
                    print(f"Error sending transaction: {e}")
        before_pool = self.current_node.getClient().tx_pool_info()
        assert successfulSize == 1
        assert before_pool['pending'] == '0x1'
        assert before_pool['proposed'] == '0x0'
        self.node_111.getClient().set_network_active(True)
        self.node_111.connected(self.current_node)
        for i in range(10):
            self.Miner.miner_with_version(self.node_111, "0x0")
        tip_number = self.node_111.getClient().get_tip_block_number()
        self.Node.wait_node_height(self.current_node, tip_number, 1000)
        pool = self.current_node.getClient().tx_pool_info()
        assert pool['pending'] == '0x0'
        assert pool['proposed'] == '0x0'
        ret = self.current_node.getClient().get_transaction(successfulTxHash)
        assert ret['tx_status']['status'] == 'rejected'

    def test_orphan_turn_pending(self):
        """
        1. 发送tx1
        2. 发送 子交易 tx(1,10) : input = tx1.input
        3. 先转发子交易到另外一个节点
        4. 查询另外一个节点pool池的orphan交易>0 ,pending = 0
        5. 发送tx1到另外一个节点
        6. 在另外一个节点查询pool 只有2笔交易
        7. 上链
        """
        TEST_PRIVATE_1 = self.Config.MINER_PRIVATE_1

        account = self.Ckb_cli.util_key_info_by_private_key(TEST_PRIVATE_1)
        self.node_111.getClient().set_network_active(False)
        tx1 = self.Ckb_cli.wallet_transfer_by_private_key(self.Config.MINER_PRIVATE_1,
                                                          account["address"]["testnet"], 100,
                                                          self.node_111.getClient().url, "1500")
        transaction1 = self.node_111.getClient().get_transaction(tx1)
        transaction1 = transaction1['transaction']
        del transaction1['hash']
        txs = []
        # 给节点1 并发发送
        for i in range(10):
            tx = self.Tx.send_transfer_self_tx_with_input([tx1], ["0x0"], TEST_PRIVATE_1,
                                                          output_count=1,
                                                          fee=1090 + i,
                                                          api_url=self.node_111.getClient().url)
            transaction = self.node_111.getClient().get_transaction(tx)
            transaction = transaction['transaction']
            del transaction['hash']
            txs.append(transaction)
        self.node_111.getClient().remove_transaction(tx1)
        self.node_111.getClient().set_network_active(True)
        successfulSize = 0
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {executor.submit(self.node_111.getClient().send_transaction, tx): tx for tx in txs}
            for future in concurrent.futures.as_completed(futures):
                tx = futures[future]
                try:
                    result = future.result()
                    # 处理返回结果
                    print(f"Transaction sent successfully: {result}")
                    successfulSize += 1
                except Exception as e:
                    print(f"Error sending transaction: {e}")
        before_pool = self.current_node.getClient().tx_pool_info()
        print(before_pool)
        time.sleep(3)
        before_pool = self.current_node.getClient().tx_pool_info()
        assert before_pool['pending'] == '0x0'
        assert before_pool['orphan'] != '0x0'
        self.current_node.getClient().send_transaction(transaction1)
        try:
            self.node_111.getClient().send_transaction(transaction1)
        except:
            pass
        before_pool = self.current_node.getClient().tx_pool_info()
        assert before_pool['pending'] == '0x2'

        for i in range(11):
            self.Miner.miner_with_version(self.node_111, "0x0")
        self.Miner.miner_until_tx_committed(self.node_111, tx1, 1000)
        tip_number = self.node_111.getClient().get_tip_block_number()
        self.Node.wait_node_height(self.current_node, tip_number, 1000)
        node111_pool = self.node_111.getClient().tx_pool_info()
        assert node111_pool['pending'] == '0x0'
        assert node111_pool['orphan'] == '0x0'
        after_pool = self.current_node.getClient().tx_pool_info()
        assert after_pool['pending'] == '0x0'
        assert after_pool['orphan'] == '0x0'

    def test_dep_tx_clean(self):
        """
        1. 发送tx1
        2. 发送tx2
        3. 发送tx21 : input = tx2.input,dep = tx1.input
        4. 发送tx11 : input = tx1.input,dep
        5. tx11 先上链
        6. 查询tx21的状态
            rejected
        """
        TEST_PRIVATE_1 = self.Config.MINER_PRIVATE_1
        TEST_PRIVATE_2 = self.Config.ACCOUNT_PRIVATE_1
        account = self.Ckb_cli.util_key_info_by_private_key(TEST_PRIVATE_1)
        account2 = self.Ckb_cli.util_key_info_by_private_key(TEST_PRIVATE_2)
        #         1. 发送tx1
        tx1 = self.Ckb_cli.wallet_transfer_by_private_key(TEST_PRIVATE_1,
                                                          account["address"]["testnet"], 100,
                                                          self.current_node.getClient().url, "1500")
        #         2. 发送tx2
        tx2 = self.Ckb_cli.wallet_transfer_by_private_key(TEST_PRIVATE_2,
                                                          account2["address"]["testnet"], 100,
                                                          self.current_node.getClient().url, "1500")
        self.Miner.miner_until_tx_committed(self.current_node, tx1)
        self.Miner.miner_until_tx_committed(self.current_node, tx2)
        tip_number = self.current_node.getClient().get_tip_block_number()
        self.Node.wait_node_height(self.node_111, tip_number, 1000)
        # 3. 发送tx21 : input = tx2.input,dep = tx1.input
        tx21_dep1 = self.Tx.send_transfer_self_tx_with_input([tx2], ["0x0"], TEST_PRIVATE_2,
                                                             output_count=1,
                                                             fee=1090,
                                                             api_url=self.current_node.getClient().url,
                                                             dep_cells=[{
                                                                 "tx_hash": tx1, "index_hex": "0x0"
                                                             }])

        # 4. 发送tx11 : input = tx1.input,dep
        tx11 = self.Tx.send_transfer_self_tx_with_input([tx1], ["0x0"], TEST_PRIVATE_1,
                                                        output_count=1,
                                                        fee=1090,
                                                        api_url=self.current_node.getClient().url)
        # 5. tx11 先上链
        self.Node.wait_get_transaction(self.node_111, tx21_dep1, 'pending')
        self.Node.wait_get_transaction(self.node_111, tx11, 'pending')
        self.node_111.getClient().remove_transaction(tx21_dep1)
        for i in range(10):
            self.Miner.miner_with_version(self.node_111, "0x0")
        pool = self.current_node.getClient().tx_pool_info()
        # 6. 查询tx21的状态
        ret = self.current_node.getClient().get_transaction(tx21_dep1)
        assert ret['tx_status']['status'] == 'rejected'
