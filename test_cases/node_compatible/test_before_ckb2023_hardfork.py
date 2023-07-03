import pytest

from framework.config import ACCOUNT_PRIVATE_1, ACCOUNT_PRIVATE_2, MINER_PRIVATE_1
from framework.helper.ckb_cli import util_key_info_by_private_key, wallet_transfer_by_private_key, cli_path
from framework.helper.contract import invoke_ckb_contract
from framework.helper.contract_util import deploy_contracts
from framework.helper.miner import make_tip_height_number, miner_with_version, miner_until_tx_committed
from framework.helper.node import wait_cluster_height, wait_get_transaction
from framework.test_cluster import Cluster
from framework.test_node import CkbNode, CkbNodeConfigPath


class TestBeforeCkb2023:
    node_current = CkbNode.init_dev_by_port(CkbNodeConfigPath.CURRENT_TEST, "node_compatible/current/node1", 8115,
                                            8225)
    node_110 = CkbNode.init_dev_by_port(CkbNodeConfigPath.V110, "node_compatible/current/node2", 8116,
                                        8226)
    nodes = [node_current, node_110]
    cluster: Cluster = Cluster(nodes)

    @classmethod
    def setup_class(cls):
        cls.cluster.prepare_all_nodes()
        cls.cluster.start_all_nodes()
        cls.cluster.connected_all_nodes()
        contracts = deploy_contracts(ACCOUNT_PRIVATE_1, cls.cluster.ckb_nodes[0])
        cls.spawn_contract = contracts["SpawnContract"]
        make_tip_height_number(cls.node_current, 100)
        wait_cluster_height(cls.cluster, 100, 100)

    @classmethod
    def teardown_class(cls):
        print("\nTeardown TestClass1")
        cls.cluster.stop_all_nodes()
        cls.cluster.clean_all_nodes()

    def test_node_sync(self):
        """
        wait all nodes sync
        - sync successful
        :return:
        """
        tip_number = self.node_current.getClient().get_tip_block_number()
        wait_cluster_height(self.cluster, tip_number, 300)

    @pytest.mark.parametrize("version,node", [(node.__str__(), node) for node in cluster.ckb_nodes])
    def test_node_miner(self, version, node):
        """
        node miner
        - sync miner block succ
        :param version:
        :param node:
        :return:
        """
        for i in range(10):
            miner_with_version(node, "0x0")
        tip_number = node.getClient().get_tip_block_number()
        wait_cluster_height(self.cluster, tip_number, 300)

    @pytest.mark.parametrize("version,node", [(node.__str__(), node) for node in cluster.ckb_nodes])
    def test_transfer(self, version, node):
        """
        send transfer tx
        - sync pending tx successful
        miner tx commit
        - sync committed tx successful
        :param version:
        :param node:
        :return:
        """
        account = util_key_info_by_private_key(account_private=ACCOUNT_PRIVATE_2)
        tx_hash = wallet_transfer_by_private_key(ACCOUNT_PRIVATE_1,
                                                 account["address"]["testnet"],
                                                 140,
                                                 node.getClient().url)
        print(f"txHash:{tx_hash}")
        transaction = node.getClient().get_transaction(tx_hash)
        assert transaction['tx_status']['status'] == 'pending'
        for query_node in self.cluster.ckb_nodes:
            wait_get_transaction(query_node, tx_hash, "pending")
        miner_until_tx_committed(node, tx_hash)
        for query_node in self.cluster.ckb_nodes:
            wait_get_transaction(query_node, tx_hash, "committed")
        print(cli_path)

    @pytest.mark.parametrize("version,node", [(node.__str__(), node) for node in cluster.ckb_nodes])
    def test_spawn_tx(self, version, node):
        """
         send spawn tx by data1 .
        - return Error: InvalidEcall(2101)
         send spawn tx by type .
        - return Error: InvalidEcall(2101)
        :param version:
        :param node:
        :return:
        """
        code_tx_hash, code_tx_index = self.spawn_contract.get_deploy_hash_and_index()
        invoke_arg, invoke_data = self.spawn_contract.get_arg_and_data("demo")
        with pytest.raises(Exception) as exc_info:
            tx_hash = invoke_ckb_contract(MINER_PRIVATE_1, code_tx_hash, code_tx_index, invoke_arg, "data1",
                                          invoke_data,
                                          api_url=node.getClient().url)
        expected_error_message = "InvalidEcall(2101)"
        assert expected_error_message in exc_info.value.args[0], \
            f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

        with pytest.raises(Exception) as exc_info:
            tx_hash = invoke_ckb_contract(MINER_PRIVATE_1, code_tx_hash, code_tx_index, invoke_arg, "type",
                                          invoke_data,
                                          api_url=node.getClient().url)
        expected_error_message = "InvalidEcall(2101)"
        assert expected_error_message in exc_info.value.args[0], \
            f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"
