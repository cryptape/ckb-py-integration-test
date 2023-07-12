import pytest

from framework.config import ACCOUNT_PRIVATE_1, ACCOUNT_PRIVATE_2, MINER_PRIVATE_1
from framework.helper.ckb_cli import util_key_info_by_private_key, wallet_transfer_by_private_key
from framework.helper.contract import invoke_ckb_contract
from framework.helper.contract_util import deploy_contracts
from framework.helper.miner import make_tip_height_number, miner_with_version, miner_until_tx_committed
from framework.helper.node import wait_cluster_height, wait_get_transaction, wait_node_height, \
    wait_cluster_sync_with_miner
from framework.test_cluster import Cluster
from framework.test_node import CkbNode, CkbNodeConfigPath


class TestAfterCkb2023:
    node_current = CkbNode.init_dev_by_port(CkbNodeConfigPath.CURRENT_TEST, "node_compatible/current/node1", 8115,
                                            8225)
    node_111 = CkbNode.init_dev_by_port(CkbNodeConfigPath.V111,
                                        "node_compatible/current/node2",
                                        8116,
                                        8226)
    node_110 = CkbNode.init_dev_by_port(CkbNodeConfigPath.V110, "node_compatible/current/node3", 8117,
                                        8227)
    nodes = [node_current, node_111, node_110]
    lt_111_nodes = [node_110]
    ge_111_nodes = [node_current, node_111]
    cluster: Cluster = Cluster(nodes)

    @classmethod
    def setup_class(cls):

        cls.cluster.prepare_all_nodes()
        cls.cluster.start_all_nodes()
        cls.cluster.connected_all_nodes()
        contracts = deploy_contracts(ACCOUNT_PRIVATE_1, cls.cluster.ckb_nodes[0])
        cls.spawn_contract = contracts["SpawnContract"]
        make_tip_height_number(cls.node_current, 1050)
        wait_cluster_sync_with_miner(cls.cluster, 300, 1050)
        heights = cls.cluster.get_all_nodes_height()
        print(f"heights:{heights}")

    def setup_method(self, method):
        """
        if tip number not eq
        roll back to min block number and restart node
        :param method:
        :return:
        """
        print("\nSetting up method", method.__name__)

        lt_111_tip_number = self.lt_111_nodes[0].getClient().get_tip_block_number()
        gt_111_tip_number = self.ge_111_nodes[0].getClient().get_tip_block_number()
        if lt_111_tip_number == gt_111_tip_number:
            return
        try:
            wait_cluster_height(self.cluster, max(lt_111_tip_number, gt_111_tip_number), 30)
            return
        except:
            heights = self.cluster.get_all_nodes_height()
            min_tip_number = min(heights)
            for node in self.cluster.ckb_nodes:
                make_tip_height_number(node, min_tip_number)
            self.cluster.restart_all_node()
            for _ in range(10):
                miner_with_version(self.node_current, "0x0")
            tip_number = self.node_current.getClient().get_tip_block_number()
            self.cluster.connected_all_nodes()
            wait_cluster_sync_with_miner(self.cluster, 300, tip_number)

    @classmethod
    def teardown_class(cls):
        print("\nTeardown TestClass1")
        heights = cls.cluster.get_all_nodes_height()
        print(heights)
        cls.cluster.stop_all_nodes()
        cls.cluster.clean_all_nodes()

    def test_node_sync(self):
        """
        not contains ckb2023, blocks synchronized after the hard fork
        - 110: sync successful
        - 111: sync successful
        :return:
        """
        wait_cluster_sync_with_miner(self.cluster, 300)

    @pytest.mark.parametrize("version,node", [(node.__str__(), node) for node in ge_111_nodes])
    def test_node_miner_0x0_in_ge_111_node(self, version, node):

        """
        node version >=  v111 node ,miner block
        - all nodes can sync block
        - v111: sync successful
        - v110: sync successful
        :param version:
        :param node:
        :return:
        """
        heights = self.cluster.get_all_nodes_height()
        max_tip_number = max(heights) + 10
        node.start_miner()
        wait_cluster_height(self.cluster, max_tip_number, 180)
        node.stop_miner()

    @pytest.mark.parametrize("version,node", [(node.__str__(), node) for node in ge_111_nodes])
    def test_node_miner_0x1_in_ge_111_node(self, version, node):

        """
        in >=  v111 node ,miner block :block version "0x1"
        - v111: sync successful
        - v110: sync failed
        :param version: ckb version
        :param node:
        :return:
        """

        for _ in range(10):
            miner_with_version(node, "0x1")
        tip_number = node.getClient().get_tip_block_number()
        for cnode in self.ge_111_nodes:
            wait_node_height(cnode, tip_number, 30)
        with pytest.raises(Exception) as exc_info:
            for cnode in self.lt_111_nodes:
                wait_node_height(cnode, tip_number, 10)
        expected_error_message = "time out"
        assert expected_error_message in \
               exc_info.value.args[0], \
            f"Expected substring '{expected_error_message}' " \
            f"not found in actual string '{exc_info.value.args[0]}'"

    @pytest.mark.parametrize("version,node", [(node.__str__(), node) for node in lt_111_nodes])
    def test_node_miner_0x0_in_lt_111_node(self, version, node):
        """
        node version < 111 ,miner block 0x0
        - v111: sync failed
        - v110: sync successful
        :param version:
        :param node:
        :return:
        """
        for i in range(10):
            miner_with_version(node, "0x0")
        tip_number = node.getClient().get_tip_block_number()
        with pytest.raises(Exception) as exc_info:
            wait_cluster_height(self.cluster, tip_number, 30)

        expected_error_message = "time out"
        assert expected_error_message in exc_info.value.args[0], \
            f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

    @pytest.mark.parametrize("version,node", [(node.__str__(), node) for node in lt_111_nodes])
    def test_node_miner_0x1_in_lt_111_node(self, version, node):
        """
        node < v111, miner with version:0x1
        - error: BlockVersionError
        :param version:
        :param node:
        :return:
        """
        with pytest.raises(Exception) as exc_info:
            miner_with_version(node, "0x1")
        expected_error_message = "BlockVersionError"
        assert expected_error_message in exc_info.value.args[0], \
            f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

    @pytest.mark.parametrize("version,node", [(node.__str__(), node) for node in ge_111_nodes])
    def test_transfer_in_ge_111_node(self, version, node):
        """
        node version >= 111  ,transfer pending tx
        - v111 : can found tx in pending
        - v110 : can't found tx in pending ,tx status: unknown
        wait  transfer  tx committed
        - v111 : can found tx in committed
        - v110: can found tx in committed
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
        for query_node in self.ge_111_nodes:
            wait_get_transaction(query_node, tx_hash, "pending")

        with pytest.raises(Exception) as exc_info:
            for query_node in self.lt_111_nodes:
                wait_get_transaction(query_node, tx_hash, "pending")

        expected_error_message = "Timeout"
        assert expected_error_message in exc_info.value.args[0], \
            f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

        miner_until_tx_committed(node, tx_hash)
        tip_number = node.getClient().get_tip_block_number()
        wait_cluster_sync_with_miner(self.cluster,100,tip_number)
        heights = self.cluster.get_all_nodes_height()
        print(f"heights:{heights}")
        for query_node in self.cluster.ckb_nodes:
            wait_get_transaction(query_node, tx_hash, "committed")

    @pytest.mark.parametrize("version,node", [(node.__str__(), node) for node in lt_111_nodes])
    def test_transfer_in_lt_111_node(self, version, node):
        """
        node version < 111  ,transfer pending tx
        - v110: found pending tx:
        - v111: can't find pending tx
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
        for query_node in self.lt_111_nodes:
            wait_get_transaction(query_node, tx_hash, "pending")

        with pytest.raises(Exception) as exc_info:
            for query_node in self.ge_111_nodes:
                wait_get_transaction(query_node, tx_hash, "pending")

        expected_error_message = "Timeout"
        assert expected_error_message in exc_info.value.args[0], \
            f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

    @pytest.mark.parametrize("version,node", [(node.__str__(), node) for node in lt_111_nodes])
    def test_spawn_tx_in_lt_111_node(self, version, node):
        """
         node version:<= 111, send spawn tx by data1 .
         - return Error: InvalidEcall(2101)
         node version:<= 111, send spawn tx by type .
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

    @pytest.mark.parametrize("version,node", [(node.__str__(), node) for node in ge_111_nodes])
    def test_transfer_data2_tx_in_ge_111_nodes(self, version, node):
        """
        before: node miner ,check all node can sync

        send tx contains data2
        - return error :
        :return:
        """

        for i in range(10):
            miner_with_version(node, "0x0")
        tip_number = node.getClient().get_tip_block_number()
        wait_cluster_sync_with_miner(self.cluster, 300, tip_number)
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
                                                 node.client.url)
        print(tx_hash)
        for cnode in self.ge_111_nodes:
            wait_get_transaction(cnode, tx_hash, "pending")

        with pytest.raises(Exception) as exc_info:
            for cnode in self.lt_111_nodes:
                wait_get_transaction(cnode, tx_hash, "pending")
        expected_error_message = "Timeout"
        assert expected_error_message in exc_info.value.args[0], \
            f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"
        miner_until_tx_committed(node, tx_hash)
        for cnode in self.ge_111_nodes:
            wait_get_transaction(cnode, tx_hash, "committed")
        lt_111_tip_number = self.lt_111_nodes[0].getClient().get_tip_block_number()
        current_tip_number = self.node_current.getClient().get_tip_block_number()
        assert current_tip_number > lt_111_tip_number
