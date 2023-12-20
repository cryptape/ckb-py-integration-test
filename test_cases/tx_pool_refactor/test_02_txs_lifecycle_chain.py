import time

import pytest
from framework.basic import CkbTest


class TestTxsLifeCycleChain(CkbTest):
    @classmethod
    def setup_class(cls):
        cls.node = cls.CkbNode.init_dev_by_port(cls.CkbNodeConfigPath.CURRENT_TEST, "tx_pool/node1", 8120,
                                            8225)
        cls.node.prepare(other_ckb_config={"ckb_tx_pool_max_tx_pool_size": "180_000"})
        cls.node.prepare()
        cls.node.start()
        cls.Miner.make_tip_height_number(cls.node, 30)

    def setup_method(self, method):
        """
        clean tx pool
        :param method:
        :return:
        """
        self.node.getClient().clear_tx_pool()

    @classmethod
    def teardown_class(cls):
        cls.node.stop()
        cls.node.clean()

    @pytest.mark.skip
    def test_high_fee_transaction_priority(self):
        """
         Transactions with higher fees are prioritized to be added to the proposals list,
            but this can result in the parent transaction being stuck in the pending stage.
                When the transaction fee of the child transaction is higher than that of the parent transaction,
                the child transaction will be prioritized and added to the proposals list.

        1. send tx father tx(fee=10000)
        2. send  1500 linked tx(fee=900000)
        3. get_block_template
            proposal length = 1500
            father tx not in proposal list
        :return:
        """
        account = self.Ckb_cli.util_key_info_by_private_key(self.Config.ACCOUNT_PRIVATE_2)
        tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(self.Config.self.Config.ACCOUNT_PRIVATE_2, account["address"]["testnet"], 3600000,
                                                 api_url=self.node.getClient().url, fee_rate="1000")
        first_tx_hash = tx_hash
        tx_list = [first_tx_hash]
        tx_hash = self.Tx.send_transfer_self_tx_with_input([tx_hash], ["0x0"], self.Config.ACCOUNT_PRIVATE_2, output_count=1500,
                                                   fee=800000,
                                                   api_url=self.node.getClient().url)
        tx_list.append(tx_hash)
        self.Node.wait_get_transaction(self.node, tx_hash, 'pending')
        # num_threads = 5
        # with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        #     futures = [executor.submit(send_transfer_self_tx_with_input,
        #                                [tx_hash], [hex(i)], self.Config.ACCOUNT_PRIVATE_2, output_count=1,
        #                                fee=9000000,
        #                                api_url=self.node.getClient().url) for i in range(0, 1500)]
        # concurrent.futures.wait(futures)

        for i in range(1500):
            self.Tx.send_transfer_self_tx_with_input([tx_hash],
                                             [hex(i)],
                                             self.Config.ACCOUNT_PRIVATE_2,
                                             output_count=1,
                                             fee=9000000,
                                             api_url=self.node.getClient().url)
        time.sleep(10)
        pool_info = self.node.getClient().tx_pool_info()
        assert int(pool_info['pending'], 16) == 1502
        print(f"pool info:{pool_info}")
        for i in range(100):
            block_template = self.node.getClient().get_block_template()
            if len(block_template['proposals']) == 1500:
                break
            time.sleep(1)
            print(f"current block proposals len:{len(block_template['proposals'])}")
        print(f"first_tx_hash:{first_tx_hash}")
        assert len(block_template['proposals']) == 1500
        assert first_tx_hash[0:22] not in list(block_template['proposals'])

    @pytest.mark.skip
    def test_01(self):
        """
        when a child transaction is confirmed on the chain, if the parent transaction is not in the proposal list,
        the parent transaction will also be added to the transaction list.
        1. send father tx
            successful
        2. send linked tx 10
            successful
        3. remove father tx in the proposals and submit block
            submit  successful
            linked tx stuck in the proposal stage.
            father tx stuck in the pending stage.
        :return:
        """
        account = self.Ckb_cli.util_key_info_by_private_key(self.Config.ACCOUNT_PRIVATE_2)
        tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(self.Config.ACCOUNT_PRIVATE_2, account["address"]["testnet"], 360000,
                                                 api_url=self.node.getClient().url, fee_rate="1000")
        first_tx_hash = tx_hash
        tx_list = [first_tx_hash]
        tx_hash = self.Tx.send_transfer_self_tx_with_input([tx_hash], ["0x0"], self.Config.ACCOUNT_PRIVATE_2, output_count=1,
                                                   fee=1000,
                                                   api_url=self.node.getClient().url)
        tx_list.append(tx_hash)
        self.Node.wait_get_transaction(self.node, tx_hash, 'pending')
        for i in range(1, 5):
            tx_hash = self.Tx.send_transfer_self_tx_with_input([tx_hash], ['0x0'], self.Config.ACCOUNT_PRIVATE_2, output_count=1,
                                                       fee=10000 * i,
                                                       api_url=self.node.getClient().url)
            tx_list.append(tx_hash)

        for i in range(200):
            block = self.node.getClient().get_block_template()
            tx_pools = self.node.getClient().get_raw_tx_pool(True)
            print("tx_pools:", len(tx_pools['pending']))
            print("transactions len:", len(block['transactions']))
            if len(block['transactions']) > 0:
                print("transactions > 1")
                break
            block['proposals'].remove(first_tx_hash[0:len('0x9b93e149e1f90a8a5436')])
            self.node.getClient().submit_block(block["work_id"], self.Miner.block_template_transfer_to_submit_block(block, '0x0'))
            for j in range(100):
                pool_info = self.node.getClient().tx_pool_info()
                tip_number = self.node.getClient().get_tip_block_number()
                if int(pool_info["tip_number"], 16) == tip_number:
                    break

        tx_pool = self.node.getClient().get_raw_tx_pool(True)
        # assert len(tx_pool['pending']) == 1
        assert first_tx_hash in list(tx_pool['pending'].keys())
