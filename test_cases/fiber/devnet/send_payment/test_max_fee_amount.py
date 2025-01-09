import pytest

from framework.basic_fiber import FiberTest


class TestMaxFeeAmount(FiberTest):
    # FiberTest.debug = True

    # @pytest.mark.skip("send to node1 -> node2 no fee 设置 max_fee = 0 会报错")
    def test_fee(self):
        account_private = self.generate_account(1000)
        self.fiber3 = self.start_new_fiber(account_private)
        self.fiber3.connect_peer(self.fiber2)
        self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(100000000 * 100000000),
                "public": True,
            }
        )
        self.wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY"
        )
        self.fiber2.get_client().open_channel(
            {
                "peer_id": self.fiber3.get_peer_id(),
                "funding_amount": hex(100000000 * 100000000),
                "public": True,
            }
        )
        self.wait_for_channel_state(
            self.fiber3.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY"
        )

        # send to node1 -> node2 no fee  max_fee = 0
        payment1 = self.fiber1.get_client().send_payment(
            {
                "target_pubkey": self.fiber2.get_client().node_info()["node_id"],
                "amount": hex(1000000 * 100000000),
                "keysend": True,
                "max_fee_amount": hex(0),
                "dry_run": True,
            }
        )
        # send to node1 - > node3 need fee 10000 but max_fee = 0

    def test_max_fee_amount_is_none(self):
        """
        max_fee_amount == node  代表什么
        Returns:

        """
