import time

import pytest

from framework.config import MINER_PRIVATE_1, ACCOUNT_PRIVATE_1, ACCOUNT_PRIVATE_2
from framework.helper.ckb_cli import util_key_info_by_private_key, wallet_transfer_by_private_key
from framework.helper.miner import make_tip_height_number, miner_with_version, miner_until_tx_committed
from framework.helper.node import wait_get_transaction
from framework.helper.tx import send_transfer_self_tx_with_input
from framework.test_node import CkbNode, CkbNodeConfigPath


class TestTxReplaceRule:

    @classmethod
    def setup_class(cls):
        cls.node = CkbNode.init_dev_by_port(CkbNodeConfigPath.CURRENT_TEST, "tx_pool/node1", 8120,
                                            8225)
        cls.node.prepare()
        cls.node.start()
        make_tip_height_number(cls.node, 30)

    def setup_method(self, method):
        """
        clean tx pool
        :param method:
        :return:
        """
        self.node.getClient().clear_tx_pool()
        for i in range(5):
            miner_with_version(self.node, "0x0")

    @classmethod
    def teardown_class(cls):
        cls.node.stop()
        cls.node.clean()

    def test_transaction_replacement_with_unconfirmed_inputs_failure(self):
        """
        replace Tx contains unconfirmed inputs, replace failed
        1. a->b ,c->d => a,d -> b
            ERROR :RBF rejected: new Tx contains unconfirmed inputs
        :return:
        """
        TEST_PRIVATE_1 = "0x98400f6a67af07025f5959af35ed653d649f745b8f54bf3f07bef9bd605ee941"

        account = util_key_info_by_private_key(TEST_PRIVATE_1)
        cell_a_hash = wallet_transfer_by_private_key(MINER_PRIVATE_1, account["address"]["testnet"], 100,
                                                     self.node.getClient().url, "1500")

        cell_c_hash = wallet_transfer_by_private_key(ACCOUNT_PRIVATE_1, account["address"]["testnet"], 100,
                                                     self.node.getClient().url, "1500")
        tx_a_to_b = send_transfer_self_tx_with_input([cell_a_hash], ['0x0'], TEST_PRIVATE_1, data="0x",
                                                     fee=5000, output_count=1,
                                                     api_url=self.node.getClient().url)
        tx_c_to_d = send_transfer_self_tx_with_input([cell_c_hash], ['0x0'], TEST_PRIVATE_1, data="0x",
                                                     fee=5000, output_count=1,
                                                     api_url=self.node.getClient().url)

        with pytest.raises(Exception) as exc_info:
            tx_ad_to_b = send_transfer_self_tx_with_input([cell_a_hash, tx_c_to_d], ['0x0', '0x0'], TEST_PRIVATE_1,
                                                          data="0x",
                                                          fee=5000, output_count=1,
                                                          api_url=self.node.getClient().url)
        expected_error_message = "RBF rejected: new Tx contains unconfirmed inputs`"
        assert expected_error_message in exc_info.value.args[0], \
            f"Expected substring '{expected_error_message}' " \
            f"not found in actual string '{exc_info.value.args[0]}'"

    def test_transaction_replacement_with_confirmed_inputs_successful(self):
        """
        replace Tx contains confirmed inputs, replace failed
        1. a->b ,c->d => a,c -> b
            ERROR :RBF rejected: new Tx contains unconfirmed inputs
        :return:
        """
        TEST_PRIVATE_1 = "0x98400f6a67af07025f5959af35ed653d649f745b8f54bf3f07bef9bd605ee941"

        account = util_key_info_by_private_key(TEST_PRIVATE_1)
        cell_a_hash = wallet_transfer_by_private_key(MINER_PRIVATE_1, account["address"]["testnet"], 100,
                                                     self.node.getClient().url, "1500")

        cell_c_hash = wallet_transfer_by_private_key(ACCOUNT_PRIVATE_1, account["address"]["testnet"], 100,
                                                     self.node.getClient().url, "1500")
        tx_a_to_b = send_transfer_self_tx_with_input([cell_a_hash], ['0x0'], TEST_PRIVATE_1, data="0x",
                                                     fee=5000, output_count=1,
                                                     api_url=self.node.getClient().url)
        tx_c_to_d = send_transfer_self_tx_with_input([cell_c_hash], ['0x0'], TEST_PRIVATE_1, data="0x",
                                                     fee=5000, output_count=1,
                                                     api_url=self.node.getClient().url)

        tx_ac_to_b = send_transfer_self_tx_with_input([cell_a_hash, cell_c_hash], ['0x0', '0x0'], TEST_PRIVATE_1,
                                                      data="0x",
                                                      fee=15000, output_count=1,
                                                      api_url=self.node.getClient().url)

        tx_a_to_b_response = self.node.getClient().get_transaction(tx_a_to_b)
        assert tx_a_to_b_response['tx_status']['status'] == 'rejected'
        assert "RBFRejected" in tx_a_to_b_response['tx_status']['reason']

        tx_c_to_d_response = self.node.getClient().get_transaction(tx_c_to_d)
        assert tx_c_to_d_response['tx_status']['status'] == 'rejected'
        assert "RBFRejected" in tx_c_to_d_response['tx_status']['reason']

        tx_ac_to_b_response = self.node.getClient().get_transaction(tx_ac_to_b)
        assert tx_ac_to_b_response['tx_status']['status'] == 'pending'

    def test_replace_fee_higher_than_min_rbf_fee(self):
        """
        min_fee < old tx fee < min_rbf_fee,replace fee must higher min_rbf_fee
        1. send tx that tx fee == min_rbf_fee
            ERROR : PoolRejctedRBF
        :return:
        """
        account = util_key_info_by_private_key(MINER_PRIVATE_1)
        hash = wallet_transfer_by_private_key(MINER_PRIVATE_1, account["address"]["testnet"], 100,
                                              self.node.getClient().url, "1000")
        self.node.getClient().get_raw_tx_pool(True)
        with pytest.raises(Exception) as exc_info:
            wallet_transfer_by_private_key(MINER_PRIVATE_1, account["address"]["testnet"], 101,
                                           self.node.getClient().url, "1500")
            self.node.getClient().get_raw_tx_pool(True)

        expected_error_message = "PoolRejctedRBF: RBF rejected: Tx's current fee is 696, expect it to be larger than: 696 to replace old txs"
        assert expected_error_message in exc_info.value.args[0], \
            f"Expected substring '{expected_error_message}' " \
            f"not found in actual string '{exc_info.value.args[0]}'"
        tx_pool = self.node.getClient().get_raw_tx_pool(True)
        hash_list = list(tx_pool['pending'].keys())
        assert tx_pool['pending'][hash_list[0]]['fee'] == '0x1d0'

    def test_transaction_fee_equal_to_old_fee(self):
        """
         min_rbf_fee < old tx fee
         1. send tx that tx fee == old tx fee
            ERROR : PoolRejctedRBF
        :return:
        """
        account = util_key_info_by_private_key(MINER_PRIVATE_1)
        hash = wallet_transfer_by_private_key(MINER_PRIVATE_1, account["address"]["testnet"], 100,
                                              self.node.getClient().url, "5000")
        self.node.getClient().get_raw_tx_pool(True)
        with pytest.raises(Exception) as exc_info:
            wallet_transfer_by_private_key(MINER_PRIVATE_1, account["address"]["testnet"], 101,
                                           self.node.getClient().url, "5000")
            self.node.getClient().get_raw_tx_pool(True)

        expected_error_message = "PoolRejctedRBF: RBF rejected: Tx's current fee is 2320, expect it to be larger than: 2320 to replace old txs"
        assert expected_error_message in exc_info.value.args[0], \
            f"Expected substring '{expected_error_message}' " \
            f"not found in actual string '{exc_info.value.args[0]}'"
        tx_pool = self.node.getClient().get_raw_tx_pool(True)
        hash_list = list(tx_pool['pending'].keys())
        assert tx_pool['pending'][hash_list[0]]['fee'] == '0x910'

    def test_transaction_replacement_higher_fee(self):
        """
        Submitting multiple transactions using the same input cell,
            the fee is higher should replace successful
        Steps:
        1. send transaction A, sending input cell to address B
             send successful
        2. send transaction B, sending the same input cell to address B and fee > A(fee)
            send successful
        3. send transaction C, sending the same input cell to address B and fee > B(fee)
            send successful
        4. query transaction (A,B,C) status
              A status : rejected ; reason : RBFRejected
              B status: rejected  ; reason : RBFRejected
              C status: pending   ;
        :return:
        """
        account = util_key_info_by_private_key(MINER_PRIVATE_1)
        tx_hash1 = wallet_transfer_by_private_key(MINER_PRIVATE_1, account["address"]["testnet"], 100,
                                                  self.node.getClient().url, "1500")
        tx_hash2 = wallet_transfer_by_private_key(MINER_PRIVATE_1, account["address"]["testnet"], 200,
                                                  self.node.getClient().url, "2000")

        tx_hash3 = wallet_transfer_by_private_key(MINER_PRIVATE_1, account["address"]["testnet"], 300,
                                                  self.node.getClient().url, "3000")
        tx1_response = self.node.getClient().get_transaction(tx_hash1)
        tx2_response = self.node.getClient().get_transaction(tx_hash2)
        tx3_response = self.node.getClient().get_transaction(tx_hash3)
        assert tx1_response['tx_status']['status'] == 'rejected'
        assert tx2_response['tx_status']['status'] == 'rejected'
        assert tx3_response['tx_status']['status'] == 'pending'
        assert "RBFRejected" in tx1_response['tx_status']['reason']
        assert "RBFRejected" in tx2_response['tx_status']['reason']

    def test_tx_conflict_too_many_txs(self):
        """
        if the replaced transaction affects more than 100 transactions, the replacement will fail.

            1. send tx A
                send tx successful
            2. send A linked tx 100
                send tx successful
            3. replace A tx
                Error : PoolRejctedRBF
            4. replace first linked tx
                replace successful

            5. query tx pool
                pending tx = 2
        :return:
        """
        account = util_key_info_by_private_key(ACCOUNT_PRIVATE_1)
        tx_hash = wallet_transfer_by_private_key(ACCOUNT_PRIVATE_1, account["address"]["testnet"], 360000,
                                                 self.node.getClient().url, "2800")
        first_hash = tx_hash
        wait_get_transaction(self.node, tx_hash, "pending")
        tx_list = []
        for i in range(100):
            tx_hash = send_transfer_self_tx_with_input([tx_hash], ["0x0"], ACCOUNT_PRIVATE_1, fee=1000,
                                                       api_url=self.node.getClient().url)
            tx_list.append(tx_hash)
            wait_get_transaction(self.node, tx_hash, "pending")
        with pytest.raises(Exception) as exc_info:
            wallet_transfer_by_private_key(ACCOUNT_PRIVATE_1, account["address"]["testnet"], 360000,
                                           self.node.getClient().url, "8800")
        expected_error_message = "Server error: PoolRejctedRBF: RBF rejected: Tx conflict too many txs, conflict txs count: 101"
        assert expected_error_message in exc_info.value.args[0], \
            f"Expected substring '{expected_error_message}' " \
            f"not found in actual string '{exc_info.value.args[0]}'"

        send_transfer_self_tx_with_input([first_hash], ["0x0"], ACCOUNT_PRIVATE_1, fee=5000,
                                         api_url=self.node.getClient().url)
        tx_pool = self.node.getClient().get_raw_tx_pool(True)
        assert len(tx_pool['pending'].keys()) == 2

    def test_replace_pending_transaction_successful(self):
        """
        replace the pending transaction,replacement successful
            1. send transaction: A
                return tx_hash_a
            2. query transaction tx_hash_a
                A status: pending
            3. replace B=>A
                return tx_hash_b
            4. query transaction tx_hash_a ，query transaction tx_hash_b
                tx_hash_a status: rejected ,reason:RBFRejected
                tx_hash_b status: pending
        :return:
        """
        account = util_key_info_by_private_key(MINER_PRIVATE_1)

        tx_a = wallet_transfer_by_private_key(MINER_PRIVATE_1, account["address"]["testnet"], 100,
                                              self.node.getClient().url, "1500")
        tx_a_response = self.node.getClient().get_transaction(tx_a)
        assert tx_a_response['tx_status']['status'] == 'pending'
        tx_b = wallet_transfer_by_private_key(MINER_PRIVATE_1, account["address"]["testnet"], 200,
                                              self.node.getClient().url, "12000")

        tx_b_response = self.node.getClient().get_transaction(tx_b)
        assert tx_b_response['tx_status']['status'] == 'pending'

        tx_a_response = self.node.getClient().get_transaction(tx_a)
        assert tx_a_response['tx_status']['status'] == 'rejected'
        assert "RBFRejected" in tx_a_response['tx_status']['reason']

    def test_replace_proposal_transaction_failure(self):
        """
        Replacing the transaction for the proposal, replacement failed.
        1. Send a transaction and submit it to the proposal.
                Query the transaction status as 'proposal.'
        2. Replace the transaction for that proposal.
            ERROR: RBF rejected: all conflict Txs should be in Pending status
        :return:
        """
        account = util_key_info_by_private_key(ACCOUNT_PRIVATE_2)
        tx_hash = wallet_transfer_by_private_key(ACCOUNT_PRIVATE_2, account["address"]["testnet"], 360000,
                                                 api_url=self.node.getClient().url, fee_rate="1000")

        tx_hash = send_transfer_self_tx_with_input([tx_hash], ["0x0"], ACCOUNT_PRIVATE_2, output_count=1,
                                                   fee=1000,
                                                   api_url=self.node.getClient().url)
        wait_get_transaction(self.node, tx_hash, 'pending')
        tx_list = [tx_hash]
        for i in range(50):
            tx_hash = send_transfer_self_tx_with_input([tx_hash], ['0x0'], ACCOUNT_PRIVATE_2, output_count=1, fee=1000,
                                                       api_url=self.node.getClient().url)
            tx_list.append(tx_hash)
        miner_with_version(self.node, "0x0")
        miner_with_version(self.node, "0x0")
        time.sleep(5)
        tx_pool = self.node.getClient().get_raw_tx_pool(True)
        for tx in tx_pool['proposed'].keys():
            print(tx)
        proposal_txs = list(tx_pool['proposed'].keys())
        assert len(proposal_txs) > 0
        for tx in proposal_txs:
            tx_response = self.node.getClient().get_transaction(tx)
            assert tx_response['tx_status']['status'] == 'proposed'
        tx_response = self.node.getClient().get_transaction(proposal_txs[0])
        with pytest.raises(Exception) as exc_info:
            send_transfer_self_tx_with_input(
                [tx_response['transaction']['inputs'][0]['previous_output']['tx_hash']], ['0x0'], ACCOUNT_PRIVATE_2,
                output_count=1,
                fee=2000,
                api_url=self.node.getClient().url)
        expected_error_message = "RBF rejected: all conflict Txs should be in Pending status"
        assert expected_error_message in exc_info.value.args[0], \
            f"Expected substring '{expected_error_message}' " \
            f"not found in actual string '{exc_info.value.args[0]}'"

        # proposal_tx_response = self.node.getClient().get_transaction(proposal_txs[0])
        # tx_response = self.node.getClient().get_transaction(tx_hash)
        # assert tx_response['tx_status']['status'] == 'pending'
        # assert proposal_tx_response['tx_status']['status'] == 'rejected'
        # tx_pool = self.node.getClient().get_raw_tx_pool(True)
        # assert proposal_txs[0] not in list(tx_pool['proposed'].keys())
        #
        # for i in range(5):
        #     miner_with_version(self.node, "0x0")
        # # miner_until_tx_committed(self.node, proposal_txs[0])
        # self.node.getClient().get_transaction(proposal_txs[0])

    def test_send_transaction_duplicate_input_with_son_tx(self):
        """
        Replacing the transaction will also remove the child transactions.
        1. send a->b ,b->c, c->d
            successful
        2. Replace a->b, a->d
            successful
        3. query get_tx_pool
            return replace tx: a->d
        4. query old txs status
            status : rejected ,reason:RBFRejected
        :return:
        """
        account = util_key_info_by_private_key(ACCOUNT_PRIVATE_1)
        tx_hash = wallet_transfer_by_private_key(ACCOUNT_PRIVATE_1, account["address"]["testnet"], 360000,
                                                 api_url=self.node.getClient().url, fee_rate="1000")
        first_tx_hash = tx_hash
        tx_list = [first_tx_hash]
        tx_hash = send_transfer_self_tx_with_input([tx_hash], ["0x0"], ACCOUNT_PRIVATE_1, output_count=1,
                                                   fee=1000,
                                                   api_url=self.node.getClient().url)
        tx_list.append(tx_hash)
        wait_get_transaction(self.node, tx_hash, 'pending')
        for i in range(5):
            tx_hash = send_transfer_self_tx_with_input([tx_hash], ['0x0'], ACCOUNT_PRIVATE_1, output_count=1, fee=1000,
                                                       api_url=self.node.getClient().url)
            tx_list.append(tx_hash)
        replace_tx_hash = wallet_transfer_by_private_key(ACCOUNT_PRIVATE_1, account["address"]["testnet"], 360000,
                                                         api_url=self.node.getClient().url, fee_rate="10000")

        tx_pool = self.node.getClient().get_raw_tx_pool(True)
        assert len(tx_pool['pending']) == 1
        assert replace_tx_hash in list(tx_pool['pending'])
        for tx in tx_list:
            tx_response = self.node.getClient().get_transaction(tx)
            assert tx_response['tx_status']['status'] == "rejected"
            assert "RBFRejected" in tx_response['tx_status']['reason']
