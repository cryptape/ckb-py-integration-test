import json
import time
from framework.basic import CkbTest


class TestTxQuery(CkbTest):

    @classmethod
    def setup_class(cls):
        cls.node = cls.CkbNode.init_dev_by_port(cls.CkbNodeConfigPath.CURRENT_TEST, "tx_pool/node1", 8120,
                                            8225)
        cls.node.prepare(other_ckb_config={"ckb_tx_pool_max_tx_pool_size": "180_000"})
        cls.node.start()
        cls.Miner.make_tip_height_number(cls.node, 100)

    @classmethod
    def teardown_class(cls):
        cls.node.stop()
        cls.node.clean()

    def test_estimate_cycles_pending_tx_successful(self):
        """
        send transaction in pending
            estimate_cycles pending tx will successful
        Steps:
        1. send transaction a-> b
        2. estimate_cycles a->b
        Result:
        1. send successful
        2. estimate_cycles successful
        :return:
        """
        account = self.Ckb_cli.util_key_info_by_private_key(self.Config.MINER_PRIVATE_1)
        tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(self.Config.MINER_PRIVATE_1, account["address"]["testnet"], 100,
                                                 self.node.getClient().url, "1900")
        print(f"txHash:{tx_hash}")
        transaction = self.node.getClient().get_transaction(tx_hash)
        del transaction['transaction']['hash']
        with open("/tmp/tmp.json", 'w') as tmp_file:
            tmp_file.write(json.dumps(transaction['transaction']))
        result = self.Ckb_cli.estimate_cycles("/tmp/tmp.json",
                                 api_url=self.node.getClient().url)
        print(f"estimate_cycles:{result}")
        print(f"pending tx cycle:{transaction['cycles']}", )
        assert int(transaction['cycles'], 16) == result
        remove_result = self.node.getClient().remove_transaction(tx_hash)
        assert remove_result == True

    def test_get_live_cell_pending_tx_input(self):
        """
        send transaction in pending ,
            estimate_cycles pending tx will successful
        Steps:
        1. send transaction a-> b
        2. estimate_cycles a->b
        Result:
        1. send successful
        2. estimate_cycles successful
        :return:
        """
        account = self.Ckb_cli.util_key_info_by_private_key(self.Config.MINER_PRIVATE_1)
        tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(self.Config.MINER_PRIVATE_1, account["address"]["testnet"], 100,
                                                 self.node.getClient().url, "1500")
        print(f"txHash:{tx_hash}")
        transaction = self.node.getClient().get_transaction(tx_hash)
        result = self.node.getClient().get_live_cell(
            transaction["transaction"]["inputs"][0]["previous_output"]["index"],
            transaction["transaction"]["inputs"][0]["previous_output"]["tx_hash"])
        assert result['status'] == 'live'
        remove_result = self.node.getClient().remove_transaction(tx_hash)
        assert remove_result == True

    def test_get_transaction_contains_fee_and_min_replace_fee_in_pending(self):
        """
        In the pending stages,
            the transaction contains the 'fee' and 'min_replace_fee' fields.
        In the proposal stages,
                the transaction contains the 'fee' ,but not contains 'min_replace_fee' fields.
        In the commit stage, both 'fee' and 'min_replace_fee' will be cleared.


        1. send tx
            successful
        2. get_transaction in pending
            contains fee and min_replace_fee
        3. miner until  get_transaction in proposed
               fee != null,  min_replace_fee == null
        4. miner until get_transaction in committed
                fee == null ,min_replace_fee == null
        :return:
        """
        account = self.Ckb_cli.util_key_info_by_private_key(self.Config.MINER_PRIVATE_1)
        tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(self.Config.MINER_PRIVATE_1, account["address"]["testnet"], 100,
                                                 self.node.getClient().url, "1500")

        tx_hash = self.Tx.send_transfer_self_tx_with_input([tx_hash], ["0x0"], self.Config.MINER_PRIVATE_1, output_count=1,
                                                   fee=1000,
                                                   api_url=self.node.getClient().url)

        print(f"txHash:{tx_hash}")
        transaction = self.node.getClient().get_transaction(tx_hash)
        tx_pool = self.node.getClient().get_raw_tx_pool(True)
        assert tx_pool['pending'][tx_hash]['fee'] == transaction['fee']
        assert int(transaction['fee'], 16) == 1000
        assert int(transaction['min_replace_fee'], 16) > 1000
        time.sleep(1)
        self.Miner.miner_with_version(self.node, "0x0")
        time.sleep(1)
        self.Miner.miner_with_version(self.node, "0x0")
        self.Node.wait_get_transaction(self.node, tx_hash, 'proposed')
        transaction = self.node.getClient().get_transaction(tx_hash)
        assert transaction['tx_status']['status'] == 'proposed'
        assert transaction['fee'] is not None
        assert transaction['min_replace_fee'] is None
        self.Miner.miner_until_tx_committed(self.node, tx_hash)
        transaction = self.node.getClient().get_transaction(tx_hash)

        assert transaction['fee'] is None
        assert transaction['min_replace_fee'] is None
