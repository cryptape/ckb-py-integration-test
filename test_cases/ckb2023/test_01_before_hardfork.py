import pytest

from framework.config import ACCOUNT_PRIVATE_1, ACCOUNT_PRIVATE_2, MINER_PRIVATE_1
from framework.helper.ckb_cli import util_key_info_by_private_key, wallet_get_capacity, wallet_transfer_by_private_key
from framework.helper.miner import miner_with_version, make_tip_height_number, miner_until_tx_committed
from framework.helper.node import wait_cluster_height
from framework.test_cluster import Cluster
from framework.test_node import CkbNode, CkbNodeConfigPath


class TestBeforeHardFork:

    @classmethod
    def setup_class(cls):
        nodes = [
            CkbNode.init_dev_by_port(CkbNodeConfigPath.CURRENT_TEST, "cluster/hardfork/node{i}".format(i=i), 8114 + i,
                                     8225 + i)
            for
            i in range(1, 5)
        ]
        cls.cluster = Cluster(nodes)
        cls.cluster.prepare_all_nodes()
        cls.cluster.start_all_nodes()
        cls.cluster.connected_all_nodes()
        make_tip_height_number(cls.cluster.ckb_nodes[0], 850)
        wait_cluster_height(cls.cluster, 850, 100)

    @classmethod
    def teardown_class(cls):
        print("\nTeardown TestClass1")
        cls.cluster.stop_all_nodes()
        cls.cluster.clean_all_nodes()

    def setup_method(self, method):
        current_epoch_result = self.cluster.ckb_nodes[0].getClient().get_current_epoch()
        consensus_response = self.cluster.ckb_nodes[0].getClient().get_consensus()
        # current epoch <  consensus epoch .length
        assert int(current_epoch_result['number'].replace("0x", "")) < get_epoch_number_by_consensus_response(
            consensus_response, '0048')

    def test_rfc_0048_in_consensus(self):
        """
        Check if the consensus response  includes RFC 0048
        -  it includes.
        :return:
        """
        consensus_response = self.cluster.ckb_nodes[0].getClient().get_consensus()
        epoch_number = get_epoch_number_by_consensus_response(consensus_response, "0048")
        assert epoch_number >= 0

    def test_rfc_0049_in_consensus(self):
        """
        Check if the consensus response  includes RFC 0049
        -  it includes.
        :return:
        """
        consensus_response = self.cluster.ckb_nodes[0].getClient().get_consensus()
        epoch_number = get_epoch_number_by_consensus_response(consensus_response, '0049')
        assert epoch_number >= 0

    def test_0048_miner_with_0x0(self):
        """
        Before the fork, the miner's block version is 0x0.
        - block mining successful.
        :return:
        """
        before_miner_num = self.cluster.ckb_nodes[0].getClient().get_tip_block_number()
        miner_with_version(self.cluster.ckb_nodes[0], "0x0")
        after_miner_num = self.cluster.ckb_nodes[0].getClient().get_tip_block_number()
        assert after_miner_num > before_miner_num

    def test_0048_miner_with_0x1(self):
        """
        Before the fork, the miner's block version is 0x1.
        - Return error : BlockVersionError
        :return:
        """
        with pytest.raises(Exception) as exc_info:
            miner_with_version(self.cluster.ckb_nodes[0], "0x1")
        expected_error_message = "BlockVersionError"
        assert expected_error_message in exc_info.value.args[0], \
            f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

    def test_0049_transfer_to_data2_address(self):
        """
        Before the fork, send a transaction with type: data2.
        - return error : "the feature \"VM Version 2\" is used in current transaction but not enabled in current chain"
        :return:
        """
        account1 = util_key_info_by_private_key(ACCOUNT_PRIVATE_1)
        account1_capacity = wallet_get_capacity(account1['address']['testnet'], self.cluster.ckb_nodes[0].client.url)
        assert account1_capacity > 0
        # send account 1 transfer data2
        # @ckb-lumos/helpers.encodeToAddress(
        #     {
        #         hashType:"data2",
        #         args:"0x",
        #         codeHash:"0x69c80d6a8104994bddc132bb568c953d60fae0ac928ad887c96de8434ca2a790"
        #     }
        # )
        # ckt1qp5usrt2syzfjj7acyetk45vj57kp7hq4jfg4ky8e9k7ss6v52neqqcnk99q8
        with pytest.raises(Exception) as exc_info:
            tx_hash = wallet_transfer_by_private_key(ACCOUNT_PRIVATE_1,
                                                     "ckt1qp5usrt2syzfjj7acyetk45vj57kp7hq4jfg4ky8e9k7ss6v52neqqcnk99q8",
                                                     140,
                                                     self.cluster.ckb_nodes[0].client.url)
        print(exc_info)
        expected_error_message = "the feature \"VM Version 2\" is used in current transaction but not enabled in current chain"
        assert expected_error_message in exc_info.value.args[0], \
            f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

    def test_0049_transfer_tx_when_10th_block_before_fork(self):
        """
        send data2 Transactions  of the 10th block before the fork:
        - Sending data2 returns the transaction hash.
        - Querying the transaction status shows it as rejected or unknown."
        :return:
        """
        consensus_response = self.cluster.ckb_nodes[0].getClient().get_consensus()
        epoch_number = get_epoch_number_by_consensus_response(consensus_response, '0049') * 1000

        make_tip_height_number(self.cluster.ckb_nodes[0], epoch_number - 10)
        wait_cluster_height(self.cluster, epoch_number - 10, 100)
        # send account 1 transfer data2
        # @ckb-lumos/helpers.encodeToAddress(
        #     {
        #         hashType:"data2",
        #         args:"0x",
        #         codeHash:"0x69c80d6a8104994bddc132bb568c953d60fae0ac928ad887c96de8434ca2a790"
        #     }
        # )
        # ckt1qp5usrt2syzfjj7acyetk45vj57kp7hq4jfg4ky8e9k7ss6v52neqqcnk99q8
        tx_hash = wallet_transfer_by_private_key(MINER_PRIVATE_1,
                                                 "ckt1qp5usrt2syzfjj7acyetk45vj57kp7hq4jfg4ky8e9k7ss6v52neqqcnk99q8",
                                                 140,
                                                 self.cluster.ckb_nodes[0].client.url)
        print(f"txHash:{tx_hash}")
        miner_with_version(self.cluster.ckb_nodes[0], "0x0")
        miner_until_tx_committed(self.cluster.ckb_nodes[0], tx_hash)
        tx_response = self.cluster.ckb_nodes[0].getClient().get_transaction(tx_hash)
        print(f"tx response:{tx_response['tx_status']['status']}")
        assert tx_response['tx_status']['status'] == "rejected" or tx_response['tx_status']['status'] == "unknown"

    def test_send_transfer_tx_when_10th_block_before_fork(self):
        """
        send transfer Transactions  of the 10th block before the fork:
        - return hash
        - Within 10 blocks before and after the fork, the transaction status is queried as: unknown.
        - After waiting for +10 blocks after the fork, the transaction  can be committed on the blockchain.
        :return:
        """
        consensus_response = self.cluster.ckb_nodes[0].getClient().get_consensus()
        epoch_number = get_epoch_number_by_consensus_response(consensus_response, '0049') * 1000

        make_tip_height_number(self.cluster.ckb_nodes[0], epoch_number - 10)
        wait_cluster_height(self.cluster, epoch_number - 10, 100)
        # send account 1 transfer data2
        # @ckb-lumos/helpers.encodeToAddress(
        #     {
        #         hashType:"data2",
        #         args:"0x",
        #         codeHash:"0x69c80d6a8104994bddc132bb568c953d60fae0ac928ad887c96de8434ca2a790"
        #     }
        # )
        # ckt1qp5usrt2syzfjj7acyetk45vj57kp7hq4jfg4ky8e9k7ss6v52neqqcnk99q8
        account = util_key_info_by_private_key(account_private=ACCOUNT_PRIVATE_2)
        tx_hash = wallet_transfer_by_private_key(ACCOUNT_PRIVATE_1,
                                                 account["address"]["testnet"],
                                                 140,
                                                 self.cluster.ckb_nodes[0].client.url)
        print(f"txHash:{tx_hash}")
        miner_until_tx_committed(self.cluster.ckb_nodes[0], tx_hash)
        tx_response = self.cluster.ckb_nodes[0].getClient().get_transaction(tx_hash)
        print(f"tx response:{tx_response['tx_status']['status']}")
        assert tx_response['tx_status']['status'] == 'unknown'
        for i in range(30):
            miner_with_version(self.cluster.ckb_nodes[0], '0x0')
        tx_response = self.cluster.ckb_nodes[0].getClient().get_transaction(tx_hash)
        print(f"tx response:{tx_response['tx_status']['status']}")
        block = self.cluster.ckb_nodes[0].getClient().get_block(tx_response['tx_status']['block_hash'])
        print(int(block["header"]["number"], 16))
        assert int(block["header"]["number"], 16) >= 1010


def get_epoch_number_by_consensus_response(consensus_response, rfc_name):
    return int(list(filter(lambda obj: rfc_name in obj['rfc'], consensus_response['hardfork_features']))[0][
                   'epoch_number'].replace("0x", ""), 16)
