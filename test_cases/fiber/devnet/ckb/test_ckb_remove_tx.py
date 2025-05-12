import time

import pytest

from framework.basic_fiber import FiberTest


class TestCkbRemoveTx(FiberTest):

    # @pytest.mark.skip("https://github.com/nervosnetwork/fiber/issues/515")
    def test_remove_open_tx_stuck_node1(self):
        """
        导致节点1 node_info 卡住

        Returns:

        """
        self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(1000 * 100000000),
                "public": True,
            }
        )
        self.wait_tx_pool(pending_size=1, try_size=100)
        self.node.client.clear_tx_pool()
        self.faucet(self.fiber1.account_private, 10000)
        time.sleep(3)
        self.open_channel(self.fiber1, self.fiber2, 1000 * 100000000, 1)

    # @pytest.mark.skip("https://github.com/nervosnetwork/fiber/issues/515")
    def test_remove_open_tx_stuck_node2(self):
        """
        导致节点2 node_info 卡住

        Returns:

        """
        self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(1000 * 100000000),
                "public": True,
            }
        )
        self.wait_tx_pool(pending_size=1, try_size=100)
        self.node.client.clear_tx_pool()
        # self.node.restart()
        # self.node.start_miner()
        time.sleep(3)
        self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(1000 * 100000000),
                "public": True,
            }
        )
        time.sleep(5)
        self.fiber2.get_client().node_info()
        fiber3 = self.start_new_fiber(self.generate_account(10000))
        self.open_channel(fiber3, self.fiber2, 1000 * 100000000, 1)
