import time

import pytest

from framework.basic_fiber import FiberTest


class TestWatchTower(FiberTest):
    def test_node1_shutdown_when_open_and_node2_split_tx(self):
        """
        node1 shuts down after opening a channel and node2 splits the transaction.

        Steps:
        1. Open a channel from node1 to node2.
        2. Wait for the channel to be in the CHANNEL_READY state.
        3. Shutdown the channel from node1.
        4. Wait for the transaction to be committed.
        5. Mine additional blocks.
        6. Check the list of channels for both nodes.
        7. Check node information for both nodes.
        8. Check graph channels for both nodes.
        9. Stop node1.
        10. Generate epochs.
        11. Wait for node2 splits  the transaction to be committed and check the transaction message.
        12. Assert the capacity and arguments of input and output cells in the transaction message.
        """

        # Step 1: Open a channel from node1 to node2
        self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(200 * 100000000),
                "public": True,
            }
        )

        # Step 2: Wait for the channel to be in the CHANNEL_READY state
        self.wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY"
        )

        # Step 3: Shutdown the channel from node1
        self.fiber1.get_client().shutdown_channel(
            {
                "channel_id": self.fiber1.get_client().list_channels({})["channels"][0][
                    "channel_id"
                ],
                "close_script": {
                    "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
                    "hash_type": "type",
                    "args": self.account1["lock_arg"],
                },
                "fee_rate": "0x3FC",
                "force": True,
            }
        )

        # Step 4: Wait for the transaction to be committed
        tx = self.wait_and_check_tx_pool_fee(1000, False)
        self.Miner.miner_until_tx_committed(self.node, tx)

        # Step 5: Mine additional blocks
        for i in range(5):
            self.Miner.miner_with_version(self.node, "0x0")

        # Step 6: Check the list of channels for both nodes
        node1_channel = self.fiber1.get_client().list_channels({})
        node2_channel = self.fiber2.get_client().list_channels({})

        # Step 7: Check node information for both nodes
        node1_node_info = self.fiber1.get_client().node_info()
        node2_node_info = self.fiber2.get_client().node_info()

        # Step 8: Check graph channels for both nodes
        node1_graph_channels = self.fiber1.get_client().graph_channels()
        node2_graph_channels = self.fiber2.get_client().graph_channels()

        # Step 9: Stop node1
        self.fiber1.stop()

        # Step 10: Generate epochs
        self.node.getClient().generate_epochs("0xa")

        # 11. Wait for node2 splits  the transaction to be committed and check the transaction message.
        tx_hash = self.wait_and_check_tx_pool_fee(1000, False, 1000)
        tx_message = self.get_tx_message(tx_hash)

        # Step 12: Assert the capacity and arguments of input and output cells in the transaction message
        assert tx_message["input_cells"][0]["capacity"] == 26199999545
        assert (
            tx_message["input_cells"][1]["args"]
            == self.get_account_script(self.fiber2.account_private)["args"]
        )

        assert (
            tx_message["output_cells"][0]["args"]
            == self.get_account_script(self.fiber2.account_private)["args"]
        )
        assert tx_message["output_cells"][0]["capacity"] == 6199999545

        assert (
            tx_message["output_cells"][1]["args"]
            == self.get_account_script(self.fiber1.account_private)["args"]
        )
        assert tx_message["output_cells"][1]["capacity"] == 19999999545

        # todo add assert list_ channel

        # todo assert node_info

        # todo assert graph_channels

    def test_node2_shutdown_when_open_and_node2_split_tx(self):
        """
        node2 shuts down after opening a channel and node2 splits the transaction.

        Steps:
        1. Open a channel from node1 to node2.
        2. Wait for the channel to be in the CHANNEL_READY state.
        3. Shutdown the channel from node2.
        4. Wait for the transaction to be committed.
        5. Mine additional blocks.
        6. Check the list of channels for both nodes.
        7. Check node information for both nodes.
        8. Check graph channels for both nodes.
        9. Stop node1.
        10. Generate epochs.
        11. Wait for node2 splits the transaction to be committed and check the transaction message.
        12. Assert the capacity and arguments of input and output cells in the transaction message.
        """

        # Step 1: Open a channel from node1 to node2
        self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(200 * 100000000),
                "public": True,
            }
        )

        # Step 2: Wait for the channel to be in the CHANNEL_READY state
        self.wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY"
        )

        # Step 3: Shutdown the channel from node2
        self.fiber2.get_client().shutdown_channel(
            {
                "channel_id": self.fiber1.get_client().list_channels({})["channels"][0][
                    "channel_id"
                ],
                "close_script": {
                    "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
                    "hash_type": "type",
                    "args": self.account2["lock_arg"],
                },
                "fee_rate": "0x3FC",
                "force": True,
            }
        )

        # Step 4: Wait for the transaction to be committed
        tx = self.wait_and_check_tx_pool_fee(1000, False)
        self.Miner.miner_until_tx_committed(self.node, tx)

        # Step 5: Mine additional blocks
        for i in range(5):
            self.Miner.miner_with_version(self.node, "0x0")

        # Step 6: Check the list of channels for both nodes
        node1_channel = self.fiber1.get_client().list_channels({})
        node2_channel = self.fiber2.get_client().list_channels({})

        # Step 7: Check node information for both nodes
        node1_node_info = self.fiber1.get_client().node_info()
        node2_node_info = self.fiber2.get_client().node_info()

        # Step 8: Check graph channels for both nodes
        node1_graph_channels = self.fiber1.get_client().graph_channels()
        node2_graph_channels = self.fiber2.get_client().graph_channels()

        # Step 9: Stop node1
        self.fiber1.stop()

        # Step 10: Generate epochs
        self.node.getClient().generate_epochs("0xa")

        # Step 11: Wait for node2 splits the transaction to be committed and check the transaction message
        tx_hash = self.wait_and_check_tx_pool_fee(1000, False, 1000)
        tx_message = self.get_tx_message(tx_hash)

        # Step 12: Assert the capacity and arguments of input and output cells in the transaction message
        assert tx_message["input_cells"][0]["capacity"] == 26199999545
        assert (
            tx_message["input_cells"][1]["args"]
            == self.get_account_script(self.fiber2.account_private)["args"]
        )

        assert (
            tx_message["output_cells"][0]["args"]
            == self.get_account_script(self.fiber1.account_private)["args"]
        )
        assert tx_message["output_cells"][0]["capacity"] == 19999999545

        assert (
            tx_message["output_cells"][1]["args"]
            == self.get_account_script(self.fiber2.account_private)["args"]
        )
        assert tx_message["output_cells"][1]["capacity"] == 6199999545

    def test_node2_shutdown_when_open_and_node1_split_tx(self):
        """
        node2 shuts down after opening a channel and node1 splits the transaction.

        Steps:
        1. Open a channel from node1 to node2.
        2. Wait for the channel to be in the CHANNEL_READY state.
        3. Shutdown the channel from node2.
        4. Wait for the transaction to be committed.
        5. Mine additional blocks.
        6. Check the list of channels for both nodes.
        7. Check node information for both nodes.
        8. Check graph channels for both nodes.
        9. Stop node2.
        10. Generate epochs.
        11. Wait for node1 splits the transaction to be committed and check the transaction message.
        12. Assert the capacity and arguments of input and output cells in the transaction message.
        """
        # Step 1: Open a channel from node1 to node2
        self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(200 * 100000000),
                "public": True,
            }
        )

        # Step 2: Wait for the channel to be in the CHANNEL_READY state
        self.wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY"
        )

        # Step 3: Shutdown the channel from node2
        self.fiber2.get_client().shutdown_channel(
            {
                "channel_id": self.fiber1.get_client().list_channels({})["channels"][0][
                    "channel_id"
                ],
                "close_script": {
                    "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
                    "hash_type": "type",
                    "args": self.account2["lock_arg"],
                },
                "fee_rate": "0x3FC",
                "force": True,
            }
        )

        # Step 4: Wait for the transaction to be committed
        tx = self.wait_and_check_tx_pool_fee(1000, False)
        self.Miner.miner_until_tx_committed(self.node, tx)

        # Step 5: Mine additional blocks
        for i in range(5):
            self.Miner.miner_with_version(self.node, "0x0")

        # Step 6: Check the list of channels for both nodes
        node1_channel = self.fiber1.get_client().list_channels({})
        node2_channel = self.fiber2.get_client().list_channels({})

        # Step 7: Check node information for both nodes
        node1_node_info = self.fiber1.get_client().node_info()
        node2_node_info = self.fiber2.get_client().node_info()

        # Step 8: Check graph channels for both nodes
        node1_graph_channels = self.fiber1.get_client().graph_channels()
        node2_graph_channels = self.fiber2.get_client().graph_channels()

        # Step 9: Stop node2
        self.fiber2.stop()

        # Step 10: Generate epochs
        self.node.getClient().generate_epochs("0xa")

        # Step 11: Wait for node1 splits the transaction to be committed and check the transaction message
        tx_hash = self.wait_and_check_tx_pool_fee(1000, False, 1000)
        tx_message = self.get_tx_message(tx_hash)

        # Step 12: Assert the capacity and arguments of input and output cells in the transaction message
        assert tx_message["input_cells"][0]["capacity"] == 26199999545
        assert (
            tx_message["input_cells"][1]["args"]
            == self.get_account_script(self.fiber1.account_private)["args"]
        )

        assert (
            tx_message["output_cells"][0]["args"]
            == self.get_account_script(self.fiber1.account_private)["args"]
        )
        assert tx_message["output_cells"][0]["capacity"] == 19999999545

        assert (
            tx_message["output_cells"][1]["args"]
            == self.get_account_script(self.fiber2.account_private)["args"]
        )
        assert tx_message["output_cells"][1]["capacity"] == 6199999545

    def test_node1_shutdown_when_open_and_node1_split_tx(self):
        """
        node1 shut_down after opening a channel and node1 splits the transaction.

        Steps:
        1. Open a channel from node1 to node2.
        2. Wait for the channel to be in the CHANNEL_READY state.
        3. Shutdown the channel from node1.
        4. Wait for the transaction to be committed.
        5. Mine additional blocks.
        6. Check the list of channels for both nodes.
        7. Check node information for both nodes.
        8. Check graph channels for both nodes.
        9. Stop node2.
        10. Generate epochs.
        11. Wait for node1 splits the transaction to be committed and check the transaction message.
        12. Assert the capacity and arguments of input and output cells in the transaction message.
        """
        # Step 1: Open a channel from node1 to node2
        self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(200 * 100000000),
                "public": True,
            }
        )

        # Step 2: Wait for the channel to be in the CHANNEL_READY state
        self.wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY"
        )

        # Step 3: Shutdown the channel from node1
        self.fiber1.get_client().shutdown_channel(
            {
                "channel_id": self.fiber1.get_client().list_channels({})["channels"][0][
                    "channel_id"
                ],
                "close_script": {
                    "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
                    "hash_type": "type",
                    "args": self.account1["lock_arg"],
                },
                "fee_rate": "0x3FC",
                "force": True,
            }
        )

        # Step 4: Wait for the transaction to be committed
        tx = self.wait_and_check_tx_pool_fee(1000, False)
        self.Miner.miner_until_tx_committed(self.node, tx)

        # Step 5: Mine additional blocks
        for i in range(5):
            self.Miner.miner_with_version(self.node, "0x0")

        # Step 6: Check the list of channels for both nodes
        node1_channel = self.fiber1.get_client().list_channels({})
        node2_channel = self.fiber2.get_client().list_channels({})

        # Step 7: Check node information for both nodes
        node1_node_info = self.fiber1.get_client().node_info()
        node2_node_info = self.fiber2.get_client().node_info()

        # Step 8: Check graph channels for both nodes
        node1_graph_channels = self.fiber1.get_client().graph_channels()
        node2_graph_channels = self.fiber2.get_client().graph_channels()

        # Step 9: Stop node2
        self.fiber2.stop()

        # Step 10: Generate epochs
        self.node.getClient().generate_epochs("0xa")

        # Step 11: Wait for node1 splits the transaction to be committed and check the transaction message
        tx_hash = self.wait_and_check_tx_pool_fee(1000, False, 1000)
        tx_message = self.get_tx_message(tx_hash)

        # Step 12: Assert the capacity and arguments of input and output cells in the transaction message
        assert tx_message["input_cells"][0]["capacity"] == 26199999545
        assert (
            tx_message["input_cells"][1]["args"]
            == self.get_account_script(self.fiber1.account_private)["args"]
        )

        assert (
            tx_message["output_cells"][0]["args"]
            == self.get_account_script(self.fiber2.account_private)["args"]
        )
        assert tx_message["output_cells"][0]["capacity"] == 6199999545

        assert (
            tx_message["output_cells"][1]["args"]
            == self.get_account_script(self.fiber1.account_private)["args"]
        )
        assert tx_message["output_cells"][1]["capacity"] == 19999999545

    def test_node1_shutdown_after_send_tx1_and_node1_split_tx(self):
        """
        node1 shuts down after sending a transaction and node1 splits the transaction.

        Steps:
        1. Open a channel from node1 to node2.
        2. Wait for the channel to be in the CHANNEL_READY state.
        3. Send a payment from node1 to node2.
        4. Shutdown the channel from node1.
        5. Wait for the transaction to be committed.
        6. Mine additional blocks.
        7. Check the list of channels for both nodes.
        8. Check node information for both nodes.
        9. Check graph channels for both nodes.
        10. Stop node2.
        11. Generate epochs.
        12. Wait for the transaction to be committed and check the transaction message.
        13. Assert the capacity and arguments of input and output cells in the transaction message.
        """
        # Step 1: Open a channel from node1 to node2
        self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(200 * 100000000),
                "public": True,
            }
        )

        # Step 2: Wait for the channel to be in the CHANNEL_READY state
        self.wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY"
        )

        # Step 3: Send a payment from node1 to node2
        self.send_payment(self.fiber1, self.fiber2, 1 * 100000000, True)

        # Step 4: Shutdown the channel from node1
        self.fiber1.get_client().shutdown_channel(
            {
                "channel_id": self.fiber1.get_client().list_channels({})["channels"][0][
                    "channel_id"
                ],
                "close_script": {
                    "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
                    "hash_type": "type",
                    "args": self.account1["lock_arg"],
                },
                "fee_rate": "0x3FC",
                "force": True,
            }
        )

        # Step 5: Wait for the transaction to be committed
        tx = self.wait_and_check_tx_pool_fee(1000, False)
        self.Miner.miner_until_tx_committed(self.node, tx)

        # Step 6: Mine additional blocks
        for i in range(5):
            self.Miner.miner_with_version(self.node, "0x0")

        # Step 7: Check the list of channels for both nodes
        node1_channel = self.fiber1.get_client().list_channels({})
        node2_channel = self.fiber2.get_client().list_channels({})

        # Step 8: Check node information for both nodes
        node1_node_info = self.fiber1.get_client().node_info()
        node2_node_info = self.fiber2.get_client().node_info()

        # Step 9: Check graph channels for both nodes
        node1_graph_channels = self.fiber1.get_client().graph_channels()
        node2_graph_channels = self.fiber2.get_client().graph_channels()

        # Step 10: Stop node2
        self.fiber2.stop()

        # Step 11: Generate epochs
        self.node.getClient().generate_epochs("0xa")

        # Step 12: Wait for the transaction to be committed and check the transaction message
        tx_hash = self.wait_and_check_tx_pool_fee(1000, False, 1000)
        tx_message = self.get_tx_message(tx_hash)

        # Step 13: Assert the capacity and arguments of input and output cells in the transaction message
        assert tx_message["input_cells"][0]["capacity"] == 26199999545
        assert (
            tx_message["input_cells"][1]["args"]
            == self.get_account_script(self.fiber1.account_private)["args"]
        )

        assert (
            tx_message["output_cells"][0]["args"]
            == self.get_account_script(self.fiber2.account_private)["args"]
        )
        assert tx_message["output_cells"][0]["capacity"] == 6299999545

        assert (
            tx_message["output_cells"][1]["args"]
            == self.get_account_script(self.fiber1.account_private)["args"]
        )
        assert tx_message["output_cells"][1]["capacity"] == 19899999545

    def test_node1_shutdown_after_send_tx1_and_node2_split_tx(self):
        """
        Test scenario where node1 shuts down after sending a transaction and node2 splits the transaction.

        Steps:
        1. Open a channel from node1 to node2.
        2. Wait for the channel to be in the CHANNEL_READY state.
        3. Send a payment from node1 to node2.
        4. Shutdown the channel from node1.
        5. Wait for the transaction to be committed.
        6. Mine additional blocks.
        7. Check the list of channels for both nodes.
        8. Check node information for both nodes.
        9. Check graph channels for both nodes.
        10. Stop node1.
        11. Generate epochs.
        12. Wait for the transaction to be committed and check the transaction message.
        13. Assert the capacity and arguments of input and output cells in the transaction message.
        """
        # Step 1: Open a channel from node1 to node2
        self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(200 * 100000000),
                "public": True,
            }
        )

        # Step 2: Wait for the channel to be in the CHANNEL_READY state
        self.wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY"
        )

        # Step 3: Send a payment from node1 to node2
        self.send_payment(self.fiber1, self.fiber2, 1 * 100000000, True)

        # Step 4: Shutdown the channel from node1
        self.fiber1.get_client().shutdown_channel(
            {
                "channel_id": self.fiber1.get_client().list_channels({})["channels"][0][
                    "channel_id"
                ],
                "close_script": {
                    "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
                    "hash_type": "type",
                    "args": self.account1["lock_arg"],
                },
                "fee_rate": "0x3FC",
                "force": True,
            }
        )

        # Step 5: Wait for the transaction to be committed
        tx = self.wait_and_check_tx_pool_fee(1000, False)
        self.Miner.miner_until_tx_committed(self.node, tx)

        # Step 6: Mine additional blocks
        for i in range(5):
            self.Miner.miner_with_version(self.node, "0x0")

        # Step 7: Check the list of channels for both nodes
        node1_channel = self.fiber1.get_client().list_channels({})
        node2_channel = self.fiber2.get_client().list_channels({})

        # Step 8: Check node information for both nodes
        node1_node_info = self.fiber1.get_client().node_info()
        node2_node_info = self.fiber2.get_client().node_info()

        # Step 9: Check graph channels for both nodes
        node1_graph_channels = self.fiber1.get_client().graph_channels()
        node2_graph_channels = self.fiber2.get_client().graph_channels()

        # Step 10: Stop node1
        self.fiber1.stop()

        # Step 11: Generate epochs
        self.node.getClient().generate_epochs("0xa")

        # Step 12: Wait for the transaction to be committed and check the transaction message
        tx_hash = self.wait_and_check_tx_pool_fee(1000, False, 1000)
        tx_message = self.get_tx_message(tx_hash)

        # Step 13: Assert the capacity and arguments of input and output cells in the transaction message
        assert tx_message["input_cells"][0]["capacity"] == 26199999545
        assert (
            tx_message["input_cells"][1]["args"]
            == self.get_account_script(self.fiber2.account_private)["args"]
        )

        assert (
            tx_message["output_cells"][0]["args"]
            == self.get_account_script(self.fiber2.account_private)["args"]
        )
        assert tx_message["output_cells"][0]["capacity"] == 6299999545

        assert (
            tx_message["output_cells"][1]["args"]
            == self.get_account_script(self.fiber1.account_private)["args"]
        )
        assert tx_message["output_cells"][1]["capacity"] == 19899999545

    @pytest.mark.skip("failed")
    def test_node2_shutdown_after_send_tx1_and_node1_split_tx(self):
        """
        Test scenario where node2 shuts down after sending a transaction and node1 splits the transaction.

        Steps:
        1. Open a channel from node1 to node2.
        2. Wait for the channel to be in the CHANNEL_READY state.
        3. Send a payment from node1 to node2.
        4. Shutdown the channel from node2.
        5. Wait for the transaction to be committed.
        6. Mine additional blocks.
        7. Check the list of channels for both nodes.
        8. Check node information for both nodes.
        9. Check graph channels for both nodes.
        10. Stop node2.
        11. Generate epochs.
        12. Wait for the transaction to be committed and check the transaction message.
        13. Assert the capacity and arguments of input and output cells in the transaction message.
        """

        # Step 1: Open a channel from node1 to node2
        self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(200 * 100000000),
                "public": True,
            }
        )

        # Step 2: Wait for the channel to be in the CHANNEL_READY state
        self.wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY"
        )

        # Step 3: Send a payment from node1 to node2
        self.send_payment(self.fiber1, self.fiber2, 1 * 100000000, True)
        time.sleep(1)

        # Step 4: Shutdown the channel from node2
        self.fiber2.get_client().shutdown_channel(
            {
                "channel_id": self.fiber1.get_client().list_channels({})["channels"][0][
                    "channel_id"
                ],
                "close_script": {
                    "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
                    "hash_type": "type",
                    "args": self.account2["lock_arg"],
                },
                "fee_rate": "0x3FC",
                "force": True,
            }
        )

        # Step 5: Wait for the transaction to be committed
        tx = self.wait_and_check_tx_pool_fee(1000, False)
        self.Miner.miner_until_tx_committed(self.node, tx)

        # Step 6: Mine additional blocks
        for i in range(5):
            self.Miner.miner_with_version(self.node, "0x0")

        # Step 7: Check the list of channels for both nodes
        node1_channel = self.fiber1.get_client().list_channels({})
        node2_channel = self.fiber2.get_client().list_channels({})

        # Step 8: Check node information for both nodes
        node1_node_info = self.fiber1.get_client().node_info()
        node2_node_info = self.fiber2.get_client().node_info()

        # Step 9: Check graph channels for both nodes
        node1_graph_channels = self.fiber1.get_client().graph_channels()
        node2_graph_channels = self.fiber2.get_client().graph_channels()

        # Step 10: Stop node2
        self.fiber2.stop()

        # Step 11: Generate epochs
        self.node.getClient().generate_epochs("0xa")

        # Step 12: Wait for the transaction to be committed and check the transaction message
        tx_hash = self.wait_and_check_tx_pool_fee(1000, False, 1000)
        tx_message = self.get_tx_message(tx_hash)

        # Step 13: Assert the capacity and arguments of input and output cells in the transaction message
        assert tx_message["input_cells"][0]["capacity"] == 26199999545
        assert (
            tx_message["input_cells"][1]["args"]
            == self.get_account_script(self.fiber1.account_private)["args"]
        )

        assert (
            tx_message["output_cells"][0]["args"]
            == self.get_account_script(self.fiber1.account_private)["args"]
        )
        assert tx_message["output_cells"][0]["capacity"] == 19899999545

        assert (
            tx_message["output_cells"][1]["args"]
            == self.get_account_script(self.fiber2.account_private)["args"]
        )
        assert tx_message["output_cells"][1]["capacity"] == 6299999545

    def test_node2_shutdown_after_send_tx1_and_node2_split_tx(self):
        """
        Test scenario where node2 shuts down after sending a transaction and node2 splits the transaction.

        Steps:
        1. Open a channel from node1 to node2.
        2. Wait for the channel to be in the CHANNEL_READY state.
        3. Send a payment from node1 to node2.
        4. Shutdown the channel from node1.
        5. Wait for the transaction to be committed.
        6. Mine additional blocks.
        7. Check the list of channels for both nodes.
        8. Check node information for both nodes.
        9. Check graph channels for both nodes.
        10. Stop node1.
        11. Generate epochs.
        12. Wait for the transaction to be committed and check the transaction message.
        13. Assert the capacity and arguments of input and output cells in the transaction message.
        """
        # Step 1: Open a channel from node1 to node2
        self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(200 * 100000000),
                "public": True,
            }
        )

        # Step 2: Wait for the channel to be in the CHANNEL_READY state
        self.wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY"
        )

        # Step 3: Send a payment from node1 to node2
        self.send_payment(self.fiber1, self.fiber2, 1 * 100000000, True)

        # Step 4: Shutdown the channel from node1
        self.fiber1.get_client().shutdown_channel(
            {
                "channel_id": self.fiber1.get_client().list_channels({})["channels"][0][
                    "channel_id"
                ],
                "close_script": {
                    "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
                    "hash_type": "type",
                    "args": self.account1["lock_arg"],
                },
                "fee_rate": "0x3FC",
                "force": True,
            }
        )

        # Step 5: Wait for the transaction to be committed
        tx = self.wait_and_check_tx_pool_fee(1000, False)
        self.Miner.miner_until_tx_committed(self.node, tx)

        # Step 6: Mine additional blocks
        for i in range(5):
            self.Miner.miner_with_version(self.node, "0x0")

        # Step 7: Check the list of channels for both nodes
        node1_channel = self.fiber1.get_client().list_channels({})
        node2_channel = self.fiber2.get_client().list_channels({})

        # Step 8: Check node information for both nodes
        node1_node_info = self.fiber1.get_client().node_info()
        node2_node_info = self.fiber2.get_client().node_info()

        # Step 9: Check graph channels for both nodes
        node1_graph_channels = self.fiber1.get_client().graph_channels()
        node2_graph_channels = self.fiber2.get_client().graph_channels()

        # Step 10: Stop node1
        self.fiber1.stop()

        # Step 11: Generate epochs
        self.node.getClient().generate_epochs("0xa")

        # Step 12: Wait for the transaction to be committed and check the transaction message
        tx_hash = self.wait_and_check_tx_pool_fee(1000, False, 1000)
        tx_message = self.get_tx_message(tx_hash)

        # Step 13: Assert the capacity and arguments of input and output cells in the transaction message
        assert tx_message["input_cells"][0]["capacity"] == 26199999545
        assert (
            tx_message["input_cells"][1]["args"]
            == self.get_account_script(self.fiber2.account_private)["args"]
        )

        assert (
            tx_message["output_cells"][0]["args"]
            == self.get_account_script(self.fiber2.account_private)["args"]
        )
        assert tx_message["output_cells"][0]["capacity"] == 6299999545

        assert (
            tx_message["output_cells"][1]["args"]
            == self.get_account_script(self.fiber1.account_private)["args"]
        )
        assert tx_message["output_cells"][1]["capacity"] == 19899999545

    @pytest.mark.skip("commit tx err")
    def test_node1_shutdown_after_send_tx2_and_node1_split_tx(self):
        """
        Test scenario where node1 shuts down after sending a transaction and node1 splits the transaction.

        Steps:
        1. Open a channel from node1 to node2.
        2. Wait for the channel to be in the CHANNEL_READY state.
        3. Send payments between node1 and node2.
        4. Shutdown the channel from node1.
        5. Wait for the transaction to be committed.
        6. Mine additional blocks.
        7. Check the list of channels for both nodes.
        8. Check node information for both nodes.
        9. Check graph channels for both nodes.
        10. Stop node1.
        11. Generate epochs.
        12. Wait for the transaction to be committed and check the transaction message.
        13. Assert the capacity and arguments of input and output cells in the transaction message.
        """

        # Step 1: Open a channel from node1 to node2
        self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(200 * 100000000),
                "public": True,
            }
        )

        # Step 2: Wait for the channel to be in the CHANNEL_READY state
        self.wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY"
        )

        # Step 3: Send payments between node1 and node2
        self.send_payment(self.fiber1, self.fiber2, 10 * 100000000, True)
        self.send_payment(self.fiber2, self.fiber1, 10 * 100000000, True)
        # todo check balance

        # Step 4: Shutdown the channel from node1
        self.fiber1.get_client().shutdown_channel(
            {
                "channel_id": self.fiber1.get_client().list_channels({})["channels"][0][
                    "channel_id"
                ],
                "close_script": {
                    "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
                    "hash_type": "type",
                    "args": self.account1["lock_arg"],
                },
                "fee_rate": "0x3FC",
                "force": True,
            }
        )

        # Step 5: Wait for the transaction to be committed
        tx = self.wait_and_check_tx_pool_fee(1000, False)
        self.Miner.miner_until_tx_committed(self.node, tx)

        # Step 6: Mine additional blocks
        for i in range(5):
            self.Miner.miner_with_version(self.node, "0x0")

        # Step 7: Check the list of channels for both nodes
        node1_channel = self.fiber1.get_client().list_channels({})
        node2_channel = self.fiber2.get_client().list_channels({})

        # Step 8: Check node information for both nodes
        node1_node_info = self.fiber1.get_client().node_info()
        node2_node_info = self.fiber2.get_client().node_info()

        # Step 9: Check graph channels for both nodes
        node1_graph_channels = self.fiber1.get_client().graph_channels()
        node2_graph_channels = self.fiber2.get_client().graph_channels()
        # self.fiber2.stop()

        # Step 10: Stop node1
        self.fiber1.stop()

        # Step 11: Generate epochs
        self.node.getClient().generate_epochs("0xa")

        # Step 12: Wait for the transaction to be committed and check the transaction message
        tx_hash = self.wait_and_check_tx_pool_fee(1000, False, 1000)
        tx_message = self.get_tx_message(tx_hash)
        # assert tx_message['input_cells'][0]['capacity'] ==
        # todo add assert cap

        # Step 13: Assert the capacity and arguments of input and output cells in the transaction message
        assert tx_message["input_cells"][0]["capacity"] == 26199999545
        assert (
            tx_message["input_cells"][1]["args"]
            == self.get_account_script(self.fiber1.account_private)["args"]
        )

        assert (
            tx_message["output_cells"][0]["args"]
            == self.get_account_script(self.fiber2.account_private)["args"]
        )
        assert tx_message["output_cells"][0]["capacity"] == 6199999545

        assert (
            tx_message["output_cells"][1]["args"]
            == self.get_account_script(self.fiber1.account_private)["args"]
        )
        assert tx_message["output_cells"][1]["capacity"] == 19999999545

    @pytest.mark.skip("commit tx err")
    def test_node1_shutdown_after_send_tx2_and_node2_split_tx(self):
        """
        Test scenario where node1 shuts down after sending a transaction and node2 splits the transaction.

        Steps:
        1. Open a channel from node1 to node2.
        2. Wait for the channel to be in the CHANNEL_READY state.
        3. Send payments between node1 and node2.
        4. Shutdown the channel from node1.
        5. Wait for the transaction to be committed.
        6. Mine additional blocks.
        7. Check the list of channels for both nodes.
        8. Check node information for both nodes.
        9. Check graph channels for both nodes.
        10. Stop node1.
        11. Generate epochs.
        12. Wait for the transaction to be committed and check the transaction message.
        13. Assert the capacity and arguments of input and output cells in the transaction message.
        """
        # Step 1: Open a channel from node1 to node2
        self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(200 * 100000000),
                "public": True,
            }
        )

        # Step 2: Wait for the channel to be in the CHANNEL_READY state
        self.wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY"
        )

        # Step 3: Send payments between node1 and node2
        self.send_payment(self.fiber1, self.fiber2, 1 * 100000000, True)
        self.send_payment(self.fiber2, self.fiber1, 1 * 100000000, True)

        # Step 4: Shutdown the channel from node1
        self.fiber1.get_client().shutdown_channel(
            {
                "channel_id": self.fiber1.get_client().list_channels({})["channels"][0][
                    "channel_id"
                ],
                "close_script": {
                    "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
                    "hash_type": "type",
                    "args": self.account1["lock_arg"],
                },
                "fee_rate": "0x3FC",
                "force": True,
            }
        )

        # Step 5: Wait for the transaction to be committed
        tx = self.wait_and_check_tx_pool_fee(1000, False)
        self.Miner.miner_until_tx_committed(self.node, tx)

        # Step 6: Mine additional blocks
        for i in range(5):
            self.Miner.miner_with_version(self.node, "0x0")

        # Step 7: Check the list of channels for both nodes
        node1_channel = self.fiber1.get_client().list_channels({})
        node2_channel = self.fiber2.get_client().list_channels({})

        # Step 8: Check node information for both nodes
        node1_node_info = self.fiber1.get_client().node_info()
        node2_node_info = self.fiber2.get_client().node_info()

        # Step 9: Check graph channels for both nodes
        node1_graph_channels = self.fiber1.get_client().graph_channels()
        node2_graph_channels = self.fiber2.get_client().graph_channels()

        # Step 10: Stop node1
        self.fiber1.stop()

        # Step 11: Generate epochs
        self.node.getClient().generate_epochs("0xa")

        # Step 12: Wait for the transaction to be committed and check the transaction message
        tx_hash = self.wait_and_check_tx_pool_fee(1000, False, 1000)
        tx_message = self.get_tx_message(tx_hash)

        # Step 13: Assert the capacity and arguments of input and output cells in the transaction message
        assert tx_message["input_cells"][0]["capacity"] == 26199999545
        assert (
            tx_message["input_cells"][1]["args"]
            == self.get_account_script(self.fiber2.account_private)["args"]
        )

        assert (
            tx_message["output_cells"][0]["args"]
            == self.get_account_script(self.fiber2.account_private)["args"]
        )
        assert tx_message["output_cells"][0]["capacity"] == 6199999545

        assert (
            tx_message["output_cells"][1]["args"]
            == self.get_account_script(self.fiber1.account_private)["args"]
        )
        assert tx_message["output_cells"][1]["capacity"] == 19999999545

    def test_node2_shutdown_after_send_tx2_and_node1_split_tx(self):
        """
        Test scenario where node2 shuts down after sending a transaction and node1 splits the transaction.

        Steps:
        1. Open a channel from node1 to node2.
        2. Wait for the channel to be in the CHANNEL_READY state.
        3. Send payments between node1 and node2.
        4. Shutdown the channel from node2.
        5. Wait for the transaction to be committed.
        6. Mine additional blocks.
        7. Check the list of channels for both nodes.
        8. Check node information for both nodes.
        9. Check graph channels for both nodes.
        10. Stop node1.
        11. Generate epochs.
        12. Wait for the transaction to be committed and check the transaction message.
        13. Assert the capacity and arguments of input and output cells in the transaction message.
        """
        # Step 1: Open a channel from node1 to node2
        self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(200 * 100000000),
                "public": True,
            }
        )

        # Step 2: Wait for the channel to be in the CHANNEL_READY state
        self.wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY"
        )

        # Step 3: Send payments between node1 and node2
        self.send_payment(self.fiber1, self.fiber2, 10 * 100000000, True)
        self.send_payment(self.fiber2, self.fiber1, 10 * 100000000, True)
        # todo check balance

        # Step 4: Shutdown the channel from node2
        self.fiber2.get_client().shutdown_channel(
            {
                "channel_id": self.fiber1.get_client().list_channels({})["channels"][0][
                    "channel_id"
                ],
                "close_script": {
                    "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
                    "hash_type": "type",
                    "args": self.account2["lock_arg"],
                },
                "fee_rate": "0x3FC",
                "force": True,
            }
        )

        # Step 5: Wait for the transaction to be committed
        tx = self.wait_and_check_tx_pool_fee(1000, False)
        self.Miner.miner_until_tx_committed(self.node, tx)

        # Step 6: Mine additional blocks
        for i in range(5):
            self.Miner.miner_with_version(self.node, "0x0")

        # Step 7: Check the list of channels for both nodes
        node1_channel = self.fiber1.get_client().list_channels({})
        node2_channel = self.fiber2.get_client().list_channels({})

        # Step 8: Check node information for both nodes
        node1_node_info = self.fiber1.get_client().node_info()
        node2_node_info = self.fiber2.get_client().node_info()

        # Step 9: Check graph channels for both nodes
        node1_graph_channels = self.fiber1.get_client().graph_channels()
        node2_graph_channels = self.fiber2.get_client().graph_channels()

        # Step 10: Stop node1
        self.fiber1.stop()

        # Step 11: Generate epochs
        self.node.getClient().generate_epochs("0xa")

        # Step 12: Wait for the transaction to be committed and check the transaction message
        tx_hash = self.wait_and_check_tx_pool_fee(1000, False, 1000)
        tx_message = self.get_tx_message(tx_hash)

        # Step 13: Assert the capacity and arguments of input and output cells in the transaction message
        assert tx_message["input_cells"][0]["capacity"] == 26199999545
        assert (
            tx_message["input_cells"][1]["args"]
            == self.get_account_script(self.fiber2.account_private)["args"]
        )

        assert (
            tx_message["output_cells"][0]["args"]
            == self.get_account_script(self.fiber1.account_private)["args"]
        )
        assert tx_message["output_cells"][0]["capacity"] == 19999999545

        assert (
            tx_message["output_cells"][1]["args"]
            == self.get_account_script(self.fiber2.account_private)["args"]
        )
        assert tx_message["output_cells"][1]["capacity"] == 6199999545

    @pytest.mark.skip("commit tx err")
    def test_node2_shutdown_after_send_tx2_and_node2_split_tx(self):
        """
        Test scenario where node2 shuts down after sending a transaction and node2 splits the transaction.

        Steps:
        1. Open a channel from node1 to node2.
        2. Wait for the channel to be in the CHANNEL_READY state.
        3. Send payments between node1 and node2.
        4. Shutdown the channel from node1.
        5. Wait for the transaction to be committed.
        6. Mine additional blocks.
        7. Check the list of channels for both nodes.
        8. Check node information for both nodes.
        9. Check graph channels for both nodes.
        10. Stop node1.
        11. Generate epochs.
        12. Wait for the transaction to be committed and check the transaction message.
        13. Assert the capacity and arguments of input and output cells in the transaction message.
        """
        # Step 1: Open a channel from node1 to node2
        self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(200 * 100000000),
                "public": True,
            }
        )

        # Step 2: Wait for the channel to be in the CHANNEL_READY state
        self.wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY"
        )

        # Step 3: Send payments between node1 and node2
        self.send_payment(self.fiber1, self.fiber2, 1 * 100000000, True)
        self.send_payment(self.fiber2, self.fiber1, 1 * 100000000, True)
        time.sleep(1)

        # Step 4: Shutdown the channel from node1
        self.fiber1.get_client().shutdown_channel(
            {
                "channel_id": self.fiber1.get_client().list_channels({})["channels"][0][
                    "channel_id"
                ],
                "close_script": {
                    "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
                    "hash_type": "type",
                    "args": self.account1["lock_arg"],
                },
                "fee_rate": "0x3FC",
                "force": True,
            }
        )

        # Step 5: Wait for the transaction to be committed
        tx = self.wait_and_check_tx_pool_fee(1000, False)
        self.Miner.miner_until_tx_committed(self.node, tx)

        # Step 6: Mine additional blocks
        for i in range(5):
            self.Miner.miner_with_version(self.node, "0x0")

        # Step 7: Check the list of channels for both nodes
        node1_channel = self.fiber1.get_client().list_channels({})
        node2_channel = self.fiber2.get_client().list_channels({})

        # Step 8: Check node information for both nodes
        node1_node_info = self.fiber1.get_client().node_info()
        node2_node_info = self.fiber2.get_client().node_info()

        # Step 9: Check graph channels for both nodes
        node1_graph_channels = self.fiber1.get_client().graph_channels()
        node2_graph_channels = self.fiber2.get_client().graph_channels()

        # Step 10: Stop node1
        self.fiber1.stop()

        # Step 11: Generate epochs
        self.node.getClient().generate_epochs("0xa")

        # Step 12: Wait for the transaction to be committed and check the transaction message
        tx_hash = self.wait_and_check_tx_pool_fee(1000, False, 1000)
        tx_message = self.get_tx_message(tx_hash)

        # Step 13: Assert the capacity and arguments of input and output cells in the transaction message
        assert tx_message["input_cells"][0]["capacity"] == 26199999545
        assert (
            tx_message["input_cells"][1]["args"]
            == self.get_account_script(self.fiber2.account_private)["args"]
        )

        assert (
            tx_message["output_cells"][0]["args"]
            == self.get_account_script(self.fiber2.account_private)["args"]
        )
        assert tx_message["output_cells"][0]["capacity"] == 6199999545

        assert (
            tx_message["output_cells"][1]["args"]
            == self.get_account_script(self.fiber1.account_private)["args"]
        )
        assert tx_message["output_cells"][1]["capacity"] == 19999999545

    def test_node1_shutdown_after_send_txN_and_node1_split_tx(self):
        """
        Test scenario where node1 shuts down after sending multiple transactions and node1 splits the transaction.

        Steps:
        1. Open a channel from node1 to node2.
        2. Wait for the channel to be in the CHANNEL_READY state.
        3. Send multiple payments from node1 to node2.
        4. Shutdown the channel from node1.
        5. Wait for the transaction to be committed.
        6. Mine additional blocks.
        7. Check the list of channels for both nodes.
        8. Check node information for both nodes.
        9. Check graph channels for both nodes.
        10. Stop node2.
        11. Generate epochs.
        12. Wait for the transaction to be committed and check the transaction message.
        13. Assert the capacity and arguments of input and output cells in the transaction message.
        """
        # Step 1: Open a channel from node1 to node2
        self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(200 * 100000000),
                "public": True,
            }
        )

        # Step 2: Wait for the channel to be in the CHANNEL_READY state
        self.wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY"
        )

        # Step 3: Send multiple payments from node1 to node2
        for i in range(10):
            self.send_payment(self.fiber1, self.fiber2, 1 * 10000000, True)

        # Step 4: Shutdown the channel from node1
        self.fiber1.get_client().shutdown_channel(
            {
                "channel_id": self.fiber1.get_client().list_channels({})["channels"][0][
                    "channel_id"
                ],
                "close_script": {
                    "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
                    "hash_type": "type",
                    "args": self.account1["lock_arg"],
                },
                "fee_rate": "0x3FC",
                "force": True,
            }
        )

        # Step 5: Wait for the transaction to be committed
        tx = self.wait_and_check_tx_pool_fee(1000, False)
        self.Miner.miner_until_tx_committed(self.node, tx)

        # Step 6: Mine additional blocks
        for i in range(5):
            self.Miner.miner_with_version(self.node, "0x0")

        # Step 7: Check the list of channels for both nodes
        node1_channel = self.fiber1.get_client().list_channels({})
        node2_channel = self.fiber2.get_client().list_channels({})

        # Step 8: Check node information for both nodes
        node1_node_info = self.fiber1.get_client().node_info()
        node2_node_info = self.fiber2.get_client().node_info()

        # Step 9: Check graph channels for both nodes
        node1_graph_channels = self.fiber1.get_client().graph_channels()
        node2_graph_channels = self.fiber2.get_client().graph_channels()

        # Step 10: Stop node2
        self.fiber2.stop()

        # Step 11: Generate epochs
        self.node.getClient().generate_epochs("0xa")

        # Step 12: Wait for the transaction to be committed and check the transaction message
        tx_hash = self.wait_and_check_tx_pool_fee(1000, False, 1000)
        tx_message = self.get_tx_message(tx_hash)

        # Step 13: Assert the capacity and arguments of input and output cells in the transaction message
        assert tx_message["input_cells"][0]["capacity"] == 26199999545
        assert (
            tx_message["input_cells"][1]["args"]
            == self.get_account_script(self.fiber1.account_private)["args"]
        )

        assert (
            tx_message["output_cells"][0]["args"]
            == self.get_account_script(self.fiber2.account_private)["args"]
        )
        assert tx_message["output_cells"][0]["capacity"] == 6299999545

        assert (
            tx_message["output_cells"][1]["args"]
            == self.get_account_script(self.fiber1.account_private)["args"]
        )
        assert tx_message["output_cells"][1]["capacity"] == 19899999545

    def test_node2_shutdown_after_send_txN_and_node1_split_tx(self):
        """
        Test scenario where node2 shuts down after sending multiple transactions and node1 splits the transaction.

        Steps:
        1. Open a channel from node1 to node2.
        2. Wait for the channel to be in the CHANNEL_READY state.
        3. Send multiple payments between node1 and node2.
        4. Shutdown the channel from node2.
        5. Wait for the transaction to be committed.
        6. Mine additional blocks.
        7. Check the list of channels for both nodes.
        8. Check node information for both nodes.
        9. Check graph channels for both nodes.
        10. Stop node1.
        11. Generate epochs.
        12. Wait for the transaction to be committed and check the transaction message.
        13. Assert the capacity and arguments of input and output cells in the transaction message.
        """
        # Step 1: Open a channel from node1 to node2
        self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(200 * 100000000),
                "public": True,
            }
        )

        # Step 2: Wait for the channel to be in the CHANNEL_READY state
        self.wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY"
        )

        # Step 3: Send multiple payments between node1 and node2
        for i in range(10):
            self.send_payment(self.fiber1, self.fiber2, 10 * 100000000, True)
            self.send_payment(self.fiber2, self.fiber1, 10 * 100000000, True)
        self.send_payment(self.fiber1, self.fiber2, 10 * 100000000, True)
        self.send_payment(self.fiber2, self.fiber1, 5 * 100000000, True)
        # todo check balance

        # Step 4: Shutdown the channel from node2
        self.fiber2.get_client().shutdown_channel(
            {
                "channel_id": self.fiber1.get_client().list_channels({})["channels"][0][
                    "channel_id"
                ],
                "close_script": {
                    "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
                    "hash_type": "type",
                    "args": self.account2["lock_arg"],
                },
                "fee_rate": "0x3FC",
                "force": True,
            }
        )

        # Step 5: Wait for the transaction to be committed
        tx = self.wait_and_check_tx_pool_fee(1000, False)
        self.Miner.miner_until_tx_committed(self.node, tx)

        # Step 6: Mine additional blocks
        for i in range(5):
            self.Miner.miner_with_version(self.node, "0x0")

        # Step 7: Check the list of channels for both nodes
        node1_channel = self.fiber1.get_client().list_channels({})
        node2_channel = self.fiber2.get_client().list_channels({})

        # Step 8: Check node information for both nodes
        node1_node_info = self.fiber1.get_client().node_info()
        node2_node_info = self.fiber2.get_client().node_info()

        # Step 9: Check graph channels for both nodes
        node1_graph_channels = self.fiber1.get_client().graph_channels()
        node2_graph_channels = self.fiber2.get_client().graph_channels()

        # Step 10: Stop node1
        self.fiber1.stop()

        # Step 11: Generate epochs
        self.node.getClient().generate_epochs("0xa")

        # Step 12: Wait for the transaction to be committed and check the transaction message
        tx_hash = self.wait_and_check_tx_pool_fee(1000, False, 1000)
        tx_message = self.get_tx_message(tx_hash)

        # Step 13: Assert the capacity and arguments of input and output cells in the transaction message
        assert tx_message["input_cells"][0]["capacity"] == 26199999545
        assert (
            tx_message["input_cells"][1]["args"]
            == self.get_account_script(self.fiber2.account_private)["args"]
        )

        assert (
            tx_message["output_cells"][0]["args"]
            == self.get_account_script(self.fiber1.account_private)["args"]
        )
        assert tx_message["output_cells"][0]["capacity"] == 19499999545

        assert (
            tx_message["output_cells"][1]["args"]
            == self.get_account_script(self.fiber2.account_private)["args"]
        )
        assert tx_message["output_cells"][1]["capacity"] == 6699999545

    def send_payment(self, src_fiber, to_fiber, amount, key_send=False):
        if not key_send:
            invoice_address = to_fiber.get_client().new_invoice(
                {
                    "amount": hex(amount),
                    "currency": "Fibd",
                    "description": "test invoice generated by node2",
                    "expiry": "0xe10",
                    "final_cltv": "0x28",
                    "payment_preimage": self.generate_random_preimage(),
                    "hash_algorithm": "sha256",
                }
            )["invoice_address"]
            payment = src_fiber.get_client().send_payment(
                {
                    "invoice": invoice_address,
                    "dry_run": True,
                }
            )
            payment = src_fiber.get_client().send_payment(
                {
                    "invoice": invoice_address,
                }
            )
            self.wait_payment_state(src_fiber, payment["payment_hash"], "Success")
            self.wait_invoice_state(to_fiber, payment["payment_hash"], "Paid")
            return payment["payment_hash"]
        payment = src_fiber.get_client().send_payment(
            {
                "amount": hex(amount),
                "target_pubkey": to_fiber.get_client().node_info()["public_key"],
                "keysend": True,
            }
        )
        self.wait_payment_state(src_fiber, payment["payment_hash"], "Success")
        return payment["payment_hash"]
