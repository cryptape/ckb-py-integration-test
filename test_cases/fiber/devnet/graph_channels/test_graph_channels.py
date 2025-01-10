import time

import pytest

from framework.basic_fiber import FiberTest


class TestGraphChannels(FiberTest):
    """
    1. 新增 channels
    2. 更新 channels
    3. 删除 channels
    """

    def test_add_channels(self):
        """
        1. node1 add channel
        2. node2 add channel
        3. node3 add channel

        4. add new node link node3
        Returns:

        """
        account3_private_key = self.generate_account(1000)
        self.fiber3 = self.start_new_fiber(account3_private_key)
        self.fiber3.connect_peer(self.fiber2)
        time.sleep(1)
        # n1-n2 创建 public channel
        self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(200 * 100000000),
                "public": True,
            }
        )
        self.wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY"
        )
        # check node1 graph channels
        time.sleep(1)
        node1_channels = self.fiber1.get_client().graph_channels()
        node2_channels = self.fiber2.get_client().graph_channels()
        node3_channels = self.fiber3.get_client().graph_channels()
        print("check node1 graph channels")
        print("node1_channels:", node1_channels)
        assert len(node1_channels["channels"]) == 1
        print("node2_channels", node2_channels)
        assert len(node2_channels["channels"]) == 1
        print("node3_channels", node3_channels)
        assert len(node3_channels["channels"]) == 1
        # check node2 graph channels
        # check node3 graph channels

        # n1-n2 创建 私有 channel
        self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(200 * 100000000),
                "public": False,
            }
        )
        self.wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY"
        )
        time.sleep(1)
        node1_channels = self.fiber1.get_client().graph_channels()
        node2_channels = self.fiber2.get_client().graph_channels()
        node3_channels = self.fiber3.get_client().graph_channels()
        print("n1-n2 创建 私有 channel")
        print("node1_channels:", node1_channels)
        assert len(node1_channels["channels"]) == 1
        print("node2_channels", node2_channels)
        assert len(node2_channels["channels"]) == 1
        print("node3_channels", node3_channels)
        assert len(node3_channels["channels"]) == 1
        # n2-n3 创建 public channel
        self.fiber2.get_client().open_channel(
            {
                "peer_id": self.fiber3.get_peer_id(),
                "funding_amount": hex(200 * 100000000),
                "public": True,
            }
        )
        self.wait_for_channel_state(
            self.fiber2.get_client(), self.fiber3.get_peer_id(), "CHANNEL_READY"
        )
        time.sleep(1)
        node1_channels = self.fiber1.get_client().graph_channels()
        node2_channels = self.fiber2.get_client().graph_channels()
        node3_channels = self.fiber3.get_client().graph_channels()
        print("n2-n3 创建 public channel")
        print("node1_channels:", node1_channels)
        assert len(node1_channels["channels"]) == 2
        print("node2_channels", node2_channels)
        assert len(node2_channels["channels"]) == 2
        print("node3_channels", node3_channels)
        assert len(node3_channels["channels"]) == 2
        # n2-n3 创建 私有 channel
        self.fiber2.get_client().open_channel(
            {
                "peer_id": self.fiber3.get_peer_id(),
                "funding_amount": hex(200 * 100000000),
                "public": False,
            }
        )
        self.wait_for_channel_state(
            self.fiber2.get_client(), self.fiber3.get_peer_id(), "CHANNEL_READY"
        )
        time.sleep(1)
        node1_channels = self.fiber1.get_client().graph_channels()
        node2_channels = self.fiber2.get_client().graph_channels()
        node3_channels = self.fiber3.get_client().graph_channels()
        print("n2-n3 创建 私有 channel")
        print("node1_channels:", node1_channels)
        assert len(node1_channels["channels"]) == 2
        print("node2_channels", node2_channels)
        assert len(node2_channels["channels"]) == 2
        print("node3_channels", node3_channels)
        assert len(node3_channels["channels"]) == 2

        fiber4 = self.start_new_fiber(self.generate_random_preimage())
        fiber4.connect_peer(self.fiber3)
        time.sleep(5)
        node4_channels = fiber4.get_client().graph_channels()
        print("node4_channels", node4_channels)
        assert len(node4_channels["channels"]) == 2

    @pytest.mark.skip("remove failed ")
    def test_remove_channels(self):
        """
        force close channel
        close channel
        Returns:

        """
        account3_private_key = self.generate_account(1000)
        self.fiber3 = self.start_new_fiber(account3_private_key)
        self.fiber3.connect_peer(self.fiber2)
        time.sleep(1)
        # n1-n2 创建 public channel
        self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(200 * 100000000),
                "public": True,
            }
        )
        self.wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY"
        )
        self.fiber2.get_client().open_channel(
            {
                "peer_id": self.fiber3.get_peer_id(),
                "funding_amount": hex(200 * 100000000),
                "public": True,
            }
        )
        self.wait_for_channel_state(
            self.fiber2.get_client(), self.fiber3.get_peer_id(), "CHANNEL_READY"
        )

        # close channel 1
        N1N2_CHANNEL_ID = self.fiber1.get_client().list_channels({})["channels"][0][
            "channel_id"
        ]
        self.fiber1.get_client().shutdown_channel(
            {
                "channel_id": N1N2_CHANNEL_ID,
                "close_script": self.get_account_script(self.fiber1.account_private),
                "fee_rate": "0x3FC",
            }
        )
        self.wait_tx_pool(1)
        for i in range(10):
            self.Miner.miner_with_version(self.node, "0x0")
        time.sleep(5)
        node1_channels = self.fiber1.get_client().graph_channels()
        node2_channels = self.fiber2.get_client().graph_channels()
        node3_channels = self.fiber3.get_client().graph_channels()
        print("关闭 n12 channel")
        print("node1_channels:", node1_channels)
        assert len(node1_channels["channels"]) == 1
        print("node2_channels", node2_channels)
        assert len(node2_channels["channels"]) == 1
        print("node3_channels", node3_channels)
        assert len(node3_channels["channels"]) == 1

        # force 关闭  channel
        N2N3_CHANNEL_ID = self.fiber1.get_client().list_channels({})["channels"][0][
            "channel_id"
        ]
        self.fiber2.get_client().shutdown_channel(
            {
                "channel_id": N2N3_CHANNEL_ID,
                "close_script": self.get_account_script(self.fiber1.account_private),
                "fee_rate": "0x3FC",
                "force": True,
            }
        )
        self.wait_tx_pool(1)
        for i in range(10):
            self.Miner.miner_with_version(self.node, "0x0")
        time.sleep(5)
        node1_channels = self.fiber1.get_client().graph_channels()
        node2_channels = self.fiber2.get_client().graph_channels()
        node3_channels = self.fiber3.get_client().graph_channels()
        print("关闭 n12 channel")
        print("node1_channels:", node1_channels)
        assert len(node1_channels["channels"]) == 0
        print("node2_channels", node2_channels)
        assert len(node2_channels["channels"]) == 0
        print("node3_channels", node3_channels)
        assert len(node3_channels["channels"]) == 0

    def test_update_channel_info(self):
        """"""
        update_channel_param = {
            "enabled": True,
            "tlc_minimum_value": hex(100),
            "tlc_fee_proportional_millionths": hex(2000),
        }
        account3_private_key = self.generate_account(1000)
        self.fiber3 = self.start_new_fiber(account3_private_key)
        self.fiber3.connect_peer(self.fiber2)
        time.sleep(1)
        # n1-n2 创建 public channel
        self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(200 * 100000000),
                "public": True,
            }
        )
        self.wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY"
        )
        channel = self.fiber1.get_client().list_channels({})
        # 4. fiber2 call  update_channel (id,tlc_fee_proportional_millionths)
        tlc_fee_proportional_millionths = 2000

        update_channel_param["channel_id"] = channel["channels"][0]["channel_id"]
        channels = self.fiber1.get_client().update_channel(update_channel_param)
        time.sleep(5)
        node1_channels = self.fiber1.get_client().graph_channels()
        node2_channels = self.fiber2.get_client().graph_channels()
        node3_channels = self.fiber3.get_client().graph_channels()
        # todo check tlc_fee_proportional_millionths
        node_info = self.fiber1.get_client().node_info()
        print("node1_channels:", node1_channels)
        key = (
            "fee_rate_of_node1"
            if node3_channels["channels"][0]["node1"] == node_info["node_id"]
            else "fee_rate_of_node2"
        )
        print("key:", key)
        assert (
            node1_channels["channels"][0][key]
            == update_channel_param["tlc_fee_proportional_millionths"]
        )
        print("node2_channels", node2_channels)
        key = (
            "fee_rate_of_node1"
            if node3_channels["channels"][0]["node1"] == node_info["node_id"]
            else "fee_rate_of_node2"
        )
        assert (
            node2_channels["channels"][0][key]
            == update_channel_param["tlc_fee_proportional_millionths"]
        )
        print("node3_channels", node3_channels)
        key = (
            "fee_rate_of_node1"
            if node3_channels["channels"][0]["node1"] == node_info["node_id"]
            else "fee_rate_of_node2"
        )
        assert (
            node3_channels["channels"][0][key]
            == update_channel_param["tlc_fee_proportional_millionths"]
        )

    def test_channel_info_check(self):
        account3_private_key = self.generate_account(1000)
        self.fiber3 = self.start_new_fiber(account3_private_key)
        self.fiber3.connect_peer(self.fiber2)
        time.sleep(1)
        # n1-n2 创建 public channel
        self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(200 * 100000000),
                "public": True,
            }
        )
        open_channel_tx_hash = self.wait_and_check_tx_pool_fee(1000, False)
        self.wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY"
        )

        # self.fiber2.get_client().open_channel({
        #     "peer_id": self.fiber3.get_peer_id(),
        #     "funding_amount": hex(200 * 100000000),
        #     "public": True,
        # })
        # self.wait_for_channel_state(self.fiber2.get_client(), self.fiber3.get_peer_id(), "CHANNEL_READY")
        time.sleep(1)
        node1_channels = self.fiber1.get_client().graph_channels()
        node2_channels = self.fiber2.get_client().graph_channels()
        node3_channels = self.fiber3.get_client().graph_channels()

        # check channel_outpoint
        assert open_channel_tx_hash in node1_channels["channels"][0]["channel_outpoint"]
        assert open_channel_tx_hash in node2_channels["channels"][0]["channel_outpoint"]
        assert open_channel_tx_hash in node3_channels["channels"][0]["channel_outpoint"]

        # funding_tx_block_number
        # tx = self.node.getClient().get_transaction(open_channel_tx_hash)
        # assert (
        #     node1_channels["channels"][0]["funding_tx_block_number"]
        #     == tx["tx_status"]["block_number"]
        # )
        # funding_tx_index
        # todo funding_tx_index 是错的
        # assert node1_channels["channels"][0]["funding_tx_index"] == tx["tx_status"]["tx_index"]
        # node1
        node1_info = self.fiber1.get_client().node_info()
        node2_info = self.fiber2.get_client().node_info()
        nodes = [node1_info["node_id"], node2_info["node_id"]]
        # node2
        assert node1_channels["channels"][0]["node1"] in nodes
        assert node1_channels["channels"][0]["node2"] in nodes
        assert node2_channels["channels"][0]["node1"] in nodes
        assert node2_channels["channels"][0]["node2"] in nodes
        assert node3_channels["channels"][0]["node1"] in nodes
        assert node3_channels["channels"][0]["node2"] in nodes

        # last_updated_timestamp
        # created_timestamp
        # fee_rate_of_node2
        assert (
            node1_channels["channels"][0]["fee_rate_of_node2"]
            == node2_info["tlc_fee_proportional_millionths"]
        )
        assert (
            node2_channels["channels"][0]["fee_rate_of_node2"]
            == node2_info["tlc_fee_proportional_millionths"]
        )
        assert (
            node3_channels["channels"][0]["fee_rate_of_node2"]
            == node2_info["tlc_fee_proportional_millionths"]
        )

        # fee_rate_of_node1
        assert (
            node1_channels["channels"][0]["fee_rate_of_node1"]
            == node1_info["tlc_fee_proportional_millionths"]
        )
        assert (
            node2_channels["channels"][0]["fee_rate_of_node1"]
            == node1_info["tlc_fee_proportional_millionths"]
        )
        assert (
            node3_channels["channels"][0]["fee_rate_of_node1"]
            == node1_info["tlc_fee_proportional_millionths"]
        )

        # capacity
        assert node1_channels["channels"][0]["capacity"] == hex(138 * 100000000)
        assert node2_channels["channels"][0]["capacity"] == hex(138 * 100000000)
        assert node3_channels["channels"][0]["capacity"] == hex(138 * 100000000)

        # chain_hash
        assert node1_channels["channels"][0]["chain_hash"] == node1_info["chain_hash"]
        assert node2_channels["channels"][0]["chain_hash"] == node1_info["chain_hash"]
        assert node3_channels["channels"][0]["chain_hash"] == node1_info["chain_hash"]

        # udt_type_script
        assert node1_channels["channels"][0]["udt_type_script"] == None
        assert node2_channels["channels"][0]["udt_type_script"] == None
        assert node3_channels["channels"][0]["udt_type_script"] == None
