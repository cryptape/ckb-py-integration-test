import time

import pytest

from framework.basic_fiber import FiberTest


class TestNodeState(FiberTest):
    """
    交易中 的节点
        强制关闭
        非强制关闭
    节点不在线
        强制关闭
        非强制关闭

    """

    # FiberTest.debug = True

    # @pytest.mark.skip("node1 send payment node4 failed")
    @pytest.mark.skip("交易发送一半，如果交易卡在Inflight，下一笔交易好像也发不出去")
    def test_shutdown_in_send_payment(self):
        """
        payment state 卡在 Inflight

        Returns:

        """
        account_private_3 = self.generate_account(1000)
        account_private_4 = self.generate_account(1000)
        self.fiber3 = self.start_new_fiber(account_private_3)
        self.fiber4 = self.start_new_fiber(account_private_4)
        self.fiber2.connect_peer(self.fiber3)
        self.fiber3.connect_peer(self.fiber4)
        self.fiber4.connect_peer(self.fiber1)
        # node1 open channel node2
        self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(200 * 100000000),
                "public": True,
            }
        )
        self.wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
        )
        # node2 open channel node3
        self.fiber2.get_client().open_channel(
            {
                "peer_id": self.fiber3.get_peer_id(),
                "funding_amount": hex(200 * 100000000),
                "public": True,
            }
        )
        self.wait_for_channel_state(
            self.fiber2.get_client(), self.fiber3.get_peer_id(), "CHANNEL_READY", 120
        )
        # node3 open channel node4
        self.fiber3.get_client().open_channel(
            {
                "peer_id": self.fiber4.get_peer_id(),
                "funding_amount": hex(200 * 100000000),
                "public": True,
            }
        )
        self.wait_for_channel_state(
            self.fiber3.get_client(), self.fiber4.get_peer_id(), "CHANNEL_READY", 120
        )
        # node4 open channel node1
        # self.fiber4.get_client().open_channel({
        #     "peer_id": self.fiber1.get_peer_id(),
        #     "funding_amount": hex(200 * 100000000),
        #     "public": True,
        # })
        # self.wait_for_channel_state(self.fiber4.get_client(), self.fiber1.get_peer_id(), "CHANNEL_READY", 120)
        time.sleep(3)
        # node1 send payment to node4
        node4_info = self.fiber4.get_client().node_info()
        fiber4_pub = node4_info["public_key"]
        payment = self.fiber1.get_client().send_payment(
            {
                "target_pubkey": fiber4_pub,
                "amount": hex(1 * 100000000),
                "keysend": True,
                # "invoice": "0x123",
            }
        )

        self.wait_payment_state(self.fiber1, payment["payment_hash"], "Success", 120)
        channels = self.fiber4.get_client().list_channels({})
        assert channels["channels"][0]["local_balance"] == hex(1 * 100000000)
        N3N4_CHANNEL_ID = self.fiber4.get_client().list_channels({})["channels"][0][
            "channel_id"
        ]

        self.fiber3.get_client().shutdown_channel(
            {
                "channel_id": N3N4_CHANNEL_ID,
                "close_script": {
                    "code_hash": "0x1bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
                    "hash_type": "type",
                    "args": self.fiber3.get_account()["lock_arg"],
                },
                "fee_rate": "0x3FC",
            }
        )
        payment = self.fiber1.get_client().send_payment(
            {
                "target_pubkey": fiber4_pub,
                "amount": hex(1 * 100000000),
                "keysend": True,
                # "invoice": "0x123",
            }
        )
        tx_hash = self.wait_and_check_tx_pool_fee(1000, False, 120)
        tx_message = self.get_tx_message(tx_hash)
        payment = self.fiber1.get_client().get_payment(
            {"payment_hash": payment["payment_hash"]}
        )
        assert payment["status"] == "Inflight"
        assert {
            "args": self.fiber4.get_account()["lock_arg"],
            "capacity": 6300000000,
        } in tx_message["output_cells"]
        payment = self.fiber1.get_client().send_payment(
            {
                "target_pubkey": self.fiber3.get_client().node_info()["public_key"],
                "amount": hex(1 * 100000000),
                "keysend": True,
                # "invoice": "0x123",
            }
        )
        self.wait_payment_state(self.fiber1, payment["payment_hash"])
