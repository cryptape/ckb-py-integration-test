from framework.config import ACCOUNT_PRIVATE_1
from framework.helper.ckb_cli import util_key_info_by_private_key, wallet_transfer_by_private_key
from framework.helper.miner import make_tip_height_number, miner_until_tx_committed
from framework.helper.node import wait_get_transaction, wait_cluster_height
from framework.helper.tx import send_transfer_self_tx_with_input
from framework.test_cluster import Cluster
from framework.test_node import CkbNode, CkbNodeConfigPath


class TestNodeBroadcast:

    @classmethod
    def setup_class(cls):
        cls.current_node = CkbNode.init_dev_by_port(CkbNodeConfigPath.CURRENT_TEST, "tx_pool/node1", 8120,
                                                    8225)
        cls.node_111 = CkbNode.init_dev_by_port(CkbNodeConfigPath.V111, "tx_pool/node2", 8121,
                                                8226)
        cls.cluster = Cluster([cls.current_node, cls.node_111])
        cls.cluster.prepare_all_nodes()
        cls.cluster.start_all_nodes()
        cls.cluster.connected_all_nodes()
        make_tip_height_number(cls.current_node, 200)
        wait_cluster_height(cls.cluster, 150, 50)

    @classmethod
    def teardown_class(cls):
        cls.cluster.stop_all_nodes()
        cls.cluster.clean_all_nodes()

    def test_111_p2p_broadcast(self):
        """
        failed replacement transactions from node 111 can be rejected for synchronization by the current node
            1. Send tx-A on node 111.
                send successful
            2. Send tx-B replace tx-A on node 111.
                two tx status: pending
            3. query tx-A,tx-B status on the node 111
                tx-B: pending
                tx-A:pending
            4. query tx-A,tx-B status on the node current
                tx-B: pending
                tx-A:reject
        :return:
        """
        account = util_key_info_by_private_key(ACCOUNT_PRIVATE_1)
        tx_hash = wallet_transfer_by_private_key(ACCOUNT_PRIVATE_1, account["address"]["testnet"], 360000,
                                                 self.node_111.getClient().url, "2800")

        tx_hash1 = send_transfer_self_tx_with_input([tx_hash], ["0x0"], ACCOUNT_PRIVATE_1, fee=3000,
                                                    api_url=self.node_111.getClient().url)

        tx_hash2 = send_transfer_self_tx_with_input([tx_hash], ["0x0"], ACCOUNT_PRIVATE_1, fee=1100,
                                                    api_url=self.node_111.getClient().url)
        wait_get_transaction(self.node_111, tx_hash1, "pending")
        wait_get_transaction(self.node_111, tx_hash2, "pending")
        wait_get_transaction(self.current_node, tx_hash, "pending")

        wait_get_transaction(self.current_node, tx_hash1, "pending")
        wait_get_transaction(self.current_node, tx_hash2, "rejected")
        miner_until_tx_committed(self.node_111, tx_hash1)
        wait_get_transaction(self.current_node, tx_hash1, "committed")

    def test_current_p2p_broadcast(self):
        """
        successful replace transactions from the current node are synchronized to node 111:
            1. send tx-A on the current node.
                Transaction tx-A is sent successfully.
            2. Send tx-B to replace tx-A on the current node.
                The replacement of tx-A with tx-B is successful.
            3. Check the status of tx-A and tx-B on the current node.
                tx-A: rejected
                tx-B: pending
            4. Check the status of tx-A and tx-B on node 111.
                tx-A: pending
                tx-B: pending
            :return:
        """
        account = util_key_info_by_private_key(ACCOUNT_PRIVATE_1)
        tx_hash = wallet_transfer_by_private_key(ACCOUNT_PRIVATE_1, account["address"]["testnet"], 360000,
                                                 self.current_node.getClient().url, "2800")

        tx_hash1 = send_transfer_self_tx_with_input([tx_hash], ["0x0"], ACCOUNT_PRIVATE_1, fee=1000,
                                                    api_url=self.current_node.getClient().url)

        wait_get_transaction(self.node_111, tx_hash1, "pending")

        tx_hash2 = send_transfer_self_tx_with_input([tx_hash], ["0x0"], ACCOUNT_PRIVATE_1, fee=3100,
                                                    api_url=self.current_node.getClient().url)

        wait_get_transaction(self.current_node, tx_hash1, "rejected")
        wait_get_transaction(self.current_node, tx_hash2, "pending")
        wait_get_transaction(self.current_node, tx_hash, "pending")

        wait_get_transaction(self.node_111, tx_hash, "pending")
        wait_get_transaction(self.node_111, tx_hash1, "pending")
        wait_get_transaction(self.node_111, tx_hash2, "pending")
        miner_until_tx_committed(self.current_node, tx_hash2)
        wait_get_transaction(self.node_111, tx_hash2, "committed")
