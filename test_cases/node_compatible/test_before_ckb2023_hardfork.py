import pytest

from framework.basic import CkbTest
from parameterized import parameterized


class TestBeforeCkb2023(CkbTest):

    node_current = CkbTest.CkbNode.init_dev_by_port(
        CkbTest.CkbNodeConfigPath.CURRENT_TEST,
        "node_compatible/current/node1",
        8115,
        8225,
    )
    node_110 = CkbTest.CkbNode.init_dev_by_port(
        CkbTest.CkbNodeConfigPath.V110, "node_compatible/current/node2", 8116, 8226
    )
    nodes = [node_current, node_110]
    cluster: CkbTest.Cluster = CkbTest.Cluster(nodes)

    @classmethod
    def setup_class(cls):
        """
        1. start 2 node that version is CURRENT_TEST and V110
        2. connected 2 node
        3. deploy  spawn contract
        4. miner 100 block
        Returns:

        """

        # 1. start 2 node that version is CURRENT_TEST and V110
        cls.cluster.prepare_all_nodes()
        cls.cluster.start_all_nodes()

        # 2. connected 2 node
        cls.cluster.connected_all_nodes()
        contracts = cls.Contract_util.deploy_contracts(
            cls.Config.ACCOUNT_PRIVATE_1, cls.cluster.ckb_nodes[0]
        )
        cls.spawn_contract = contracts["SpawnContract"]

        # 3. miner 100 block
        cls.Miner.make_tip_height_number(cls.node_current, 100)
        cls.Node.wait_cluster_height(cls.cluster, 100, 100)

    @classmethod
    def teardown_class(cls):
        print("\nTeardown TestClass1")
        cls.cluster.stop_all_nodes()
        cls.cluster.clean_all_nodes()

    def test_01_node_sync(self):
        """
        wait all nodes sync
        - sync successful
        :return:
        """
        # 1. wait all nodes sync
        tip_number = self.node_current.getClient().get_tip_block_number()
        self.Node.wait_cluster_height(self.cluster, tip_number, 300)

    @parameterized.expand([(node.__str__(), node) for node in cluster.ckb_nodes])
    def test_02_node_miner(self, version, node):
        """
        node miner
        - sync miner block succ
        :param version:
        :param node:
        :return:

        1. miner 10 block
        2. wait other nodes sync
        """

        # 1. miner 10 block
        for i in range(10):
            self.Miner.miner_with_version(node, "0x0")

        # 2. wait other nodes sync
        tip_number = node.getClient().get_tip_block_number()
        self.Node.wait_cluster_height(self.cluster, tip_number, 300)

    @parameterized.expand([(node.__str__(), node) for node in cluster.ckb_nodes])
    def test_03_transfer(self, version, node):
        """
        send transfer tx
        - sync pending tx successful
        miner tx commit
        - sync committed tx successful
        :param version:
        :param node:
        :return:
        """

        # 1. send transfer tx
        account = self.Ckb_cli.util_key_info_by_private_key(
            account_private=self.Config.ACCOUNT_PRIVATE_2
        )
        tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(
            self.Config.ACCOUNT_PRIVATE_1,
            account["address"]["testnet"],
            140,
            node.getClient().url,
        )
        print(f"txHash:{tx_hash}")
        transaction = node.getClient().get_transaction(tx_hash)
        assert transaction["tx_status"]["status"] == "pending"
        for query_node in self.cluster.ckb_nodes:
            self.Node.wait_get_transaction(query_node, tx_hash, "pending")

        # 2. miner tx commit
        self.Miner.miner_until_tx_committed(node, tx_hash)
        for query_node in self.cluster.ckb_nodes:
            self.Node.wait_get_transaction(query_node, tx_hash, "committed")
        print(self.Ckb_cli.cli_path)

    @parameterized.expand([(node.__str__(), node) for node in cluster.ckb_nodes])
    def test_04_spawn_tx(self, version, node):
        """
        1. send spawn tx by data1 .
        - return Error: InvalidEcall(2603)
        2.  send spawn tx by type .
        - return Error: InvalidEcall(2603)
        :param version:
        :param node:
        :return:
        """

        # 1. send spawn tx by data1 .
        code_tx_hash, code_tx_index = self.spawn_contract.get_deploy_hash_and_index()
        invoke_arg, invoke_data = self.spawn_contract.get_arg_and_data("demo")
        with pytest.raises(Exception) as exc_info:
            self.Contract.invoke_ckb_contract(
                self.Config.MINER_PRIVATE_1,
                code_tx_hash,
                code_tx_index,
                invoke_arg,
                "data1",
                invoke_data,
                api_url=node.getClient().url,
            )
        expected_error_message = "InvalidEcall(2603)"
        assert (
            expected_error_message in exc_info.value.args[0]
        ), f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

        # 2.  send spawn tx by type .
        with pytest.raises(Exception) as exc_info:
            self.Contract.invoke_ckb_contract(
                self.Config.MINER_PRIVATE_1,
                code_tx_hash,
                code_tx_index,
                invoke_arg,
                "type",
                invoke_data,
                api_url=node.getClient().url,
            )
        expected_error_message = "InvalidEcall(2603)"
        assert (
            expected_error_message in exc_info.value.args[0]
        ), f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"
