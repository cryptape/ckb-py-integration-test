import pytest

from framework.config import ACCOUNT_PRIVATE_2, ACCOUNT_PRIVATE_1, MINER_PRIVATE_1
from framework.helper.ckb_cli import util_key_info_by_private_key, wallet_transfer_by_private_key
from framework.helper.contract import invoke_ckb_contract
from framework.helper.miner import make_tip_height_number, miner_with_version, miner_until_tx_committed
from framework.helper.node import wait_cluster_height
from framework.helper.spawn_contract import SpawnContract
from framework.test_cluster import Cluster
from framework.test_node import CkbNode, CkbNodeConfigPath


class TestAfterHardFork:

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
        make_tip_height_number(cls.cluster.ckb_nodes[0], 500)
        wait_cluster_height(cls.cluster, 500, 100)
        spawn_contract = SpawnContract()
        cls.spawn_contract = spawn_contract
        cls.spawn_contract.deploy(ACCOUNT_PRIVATE_1,cls.cluster.ckb_nodes[0])
        make_tip_height_number(cls.cluster.ckb_nodes[0], 1000)
        wait_cluster_height(cls.cluster, 1000, 100)


    @classmethod
    def teardown_class(cls):
        print("\nTeardown TestClass1")
        cls.cluster.stop_all_nodes()
        cls.cluster.clean_all_nodes()

    def setup_method(self, method):
        current_epoch_result = self.cluster.ckb_nodes[0].getClient().get_current_epoch()
        consensus_response = self.cluster.ckb_nodes[0].getClient().get_consensus()
        # current epoch <  consensus epoch .length
        assert int(current_epoch_result['number'].replace("0x", "")) >= get_epoch_number_by_consensus_response(
            consensus_response, '0048')

    def test_0048_block_version_0x(self):
        """
        After the fork, the miner's block version is 0x0.
        - block mining successful.
        :return:
        """
        before_miner_num = self.cluster.ckb_nodes[0].getClient().get_tip_block_number()
        miner_with_version(self.cluster.ckb_nodes[0], "0x0")
        after_miner_num = self.cluster.ckb_nodes[0].getClient().get_tip_block_number()
        assert after_miner_num > before_miner_num

    def test_0048_block_version_0x1(self):
        """
            After the fork, the miner's block version is 0x1.
            - block mining successful.
           :return:
        """
        before_miner_num = self.cluster.ckb_nodes[0].getClient().get_tip_block_number()
        miner_with_version(self.cluster.ckb_nodes[0], "0x1")
        after_miner_num = self.cluster.ckb_nodes[0].getClient().get_tip_block_number()
        assert after_miner_num > before_miner_num

    def test_0048_block_version_0xffffff(self):
        """
            After the fork, the miner's block version is 0xffffff.
            - block mining successful.
           :return:
        """
        before_miner_num = self.cluster.ckb_nodes[0].getClient().get_tip_block_number()
        miner_with_version(self.cluster.ckb_nodes[0], "0xffffffff")
        after_miner_num = self.cluster.ckb_nodes[0].getClient().get_tip_block_number()
        assert after_miner_num > before_miner_num

    def test_0048_block_version_0x100000000(self):
        """
            After the fork, the miner's block version is 0x100000000.
           - error : number too large to fit
           :return:
        """
        with pytest.raises(Exception) as exc_info:
            miner_with_version(self.cluster.ckb_nodes[0], "0x100000000")
        expected_error_message = "number too large to fit"
        assert expected_error_message in exc_info.value.args[0], \
            f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

    def test_send_tx_when_after_0th_fork(self):
        """
            The first block sends a regular transaction.
            - return tx_hash
            - The transaction status is queried as unknown for the first ten blocks.
            - The transaction will be committed on the blockchain after ten blocks.
            :return:
        """
        for node in self.cluster.ckb_nodes:
            make_tip_height_number(node, 1000)
        account = util_key_info_by_private_key(account_private=ACCOUNT_PRIVATE_2)
        tx_hash = wallet_transfer_by_private_key(ACCOUNT_PRIVATE_1,
                                                 account["address"]["testnet"],
                                                 140,
                                                 self.cluster.ckb_nodes[0].client.url)
        print(f"txHash:{tx_hash}")
        miner_with_version(self.cluster.ckb_nodes[0], '0x0')
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

    def test_0049_send_data2_tx(self):
        """
        After a period of hard fork, a data2 transaction is sent.
        - return tx_hash
        - The transaction will be committed on the blockchain
        :return:
        """
        # send account 1 transfer data2
        # @ckb-lumos/helpers.encodeToAddress(
        #     {
        #         hashType:"data2",
        #         args:"0x",
        #         codeHash:"0x69c80d6a8104994bddc132bb568c953d60fae0ac928ad887c96de8434ca2a790"
        #     }
        # )
        # ckt1qp5usrt2syzfjj7acyetk45vj57kp7hq4jfg4ky8e9k7ss6v52neqqcnk99q8
        for i in range(10):
            miner_with_version(self.cluster.ckb_nodes[0], "0x0")
        tx_hash = wallet_transfer_by_private_key(MINER_PRIVATE_1,
                                                 "ckt1qp5usrt2syzfjj7acyetk45vj57kp7hq4jfg4ky8e9k7ss6v52neqqcnk99q8",
                                                 140,
                                                 self.cluster.ckb_nodes[0].client.url)
        print(f"txHash:{tx_hash}")
        miner_with_version(self.cluster.ckb_nodes[0], "0x0")
        miner_until_tx_committed(self.cluster.ckb_nodes[0], tx_hash)
        tx_response = self.cluster.ckb_nodes[0].getClient().get_transaction(tx_hash)
        print(f"tx response:{tx_response['tx_status']['status']}")
        assert tx_response['tx_status']['status'] == "committed"

    def test__0050_spawn_use_data2(self):
        """
            After a period of hard fork,send spawn tx by data2 .
            - return tx_hash
            - The transaction will be committed on the blockchain
        :return:
        """
        for i in range(11):
            miner_with_version(self.cluster.ckb_nodes[0], "0x0")

        code_tx_hash,code_tx_index = self.spawn_contract.get_deploy_hash_and_index()
        invoke_arg,invoke_data = self.spawn_contract.get_arg_and_data("demo")
        tx_hash = invoke_ckb_contract(MINER_PRIVATE_1,code_tx_hash,code_tx_index,invoke_arg,"data2",invoke_data,api_url=self.cluster.ckb_nodes[0].getClient().url)
        miner_until_tx_committed(self.cluster.ckb_nodes[0],tx_hash)

    def test_0050_spawn_use_data1(self):
        """
        After a period of hard fork,send spawn tx by data1 .
            - return Error: InvalidEcall(2101)
        :return:
        """
        code_tx_hash,code_tx_index = self.spawn_contract.get_deploy_hash_and_index()
        invoke_arg, invoke_data = self.spawn_contract.get_arg_and_data("demo")
        with pytest.raises(Exception) as exc_info:
            tx_hash = invoke_ckb_contract(MINER_PRIVATE_1, code_tx_hash, code_tx_index, invoke_arg, "data1", invoke_data,
                                      api_url=self.cluster.ckb_nodes[0].getClient().url)
        expected_error_message = "InvalidEcall(2101)"
        assert expected_error_message in exc_info.value.args[0], \
            f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

    def test_0050_spawn_use_data(self):
        """
          After a period of hard fork,send spawn tx by data1 .
            - return Error: InvalidInstruction
        :return:
        """
        code_tx_hash,code_tx_index = self.spawn_contract.get_deploy_hash_and_index()
        invoke_arg, invoke_data = self.spawn_contract.get_arg_and_data("demo")
        with pytest.raises(Exception) as exc_info:
            tx_hash = invoke_ckb_contract(MINER_PRIVATE_1, code_tx_hash, code_tx_index, invoke_arg, "data", invoke_data,
                                      api_url=self.cluster.ckb_nodes[0].getClient().url)
        expected_error_message = "InvalidInstruction"
        assert expected_error_message in exc_info.value.args[0], \
            f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

    def test_0050_spawn_use_type(self):
        """
        After a period of hard fork,send spawn tx by data1 .
        - return tx_hash
        - The transaction will be committed on the blockchain
        :return:
        """
        for i in range(11):
            miner_with_version(self.cluster.ckb_nodes[0], "0x0")

        code_tx_hash, code_tx_index = self.spawn_contract.get_deploy_hash_and_index()
        invoke_arg, invoke_data = self.spawn_contract.get_arg_and_data("demo")
        tx_hash = invoke_ckb_contract(MINER_PRIVATE_1, code_tx_hash, code_tx_index, invoke_arg, "type", invoke_data,
                                      api_url=self.cluster.ckb_nodes[0].getClient().url)
        miner_until_tx_committed(self.cluster.ckb_nodes[0], tx_hash)


def get_epoch_number_by_consensus_response(consensus_response, rfc_name):
    return int(list(filter(lambda obj: rfc_name in obj['rfc'], consensus_response['hardfork_features']))[0][
                   'epoch_number'].replace("0x", ""), 16)
