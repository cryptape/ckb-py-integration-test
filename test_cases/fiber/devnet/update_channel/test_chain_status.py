import pytest

from framework.basic_fiber import FiberTest


class TestChainStatus(FiberTest):

    @pytest.mark.skip("https://github.com/nervosnetwork/fiber/issues/352")
    def test_chain_status_pending(self):
        self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(500 * 100000000),
                "public": True,
            }
        )
        # // AWAITING_TX_SIGNATURES
        self.wait_for_channel_state(
            self.fiber1.get_client(),
            self.fiber2.get_peer_id(),
            "AWAITING_TX_SIGNATURES",
        )

        # self.fiber2.get_client().update_channel({
        #     "channel_id": self.fiber1.get_client().list_channels({})["channels"][0]["channel_id"],
        #     "tlc_fee_proportional_millionths": hex(2000),
        # })
        self.fiber1.get_client().update_channel(
            {
                "channel_id": self.fiber1.get_client().list_channels({})["channels"][0][
                    "channel_id"
                ],
                "tlc_fee_proportional_millionths": hex(2000),
            }
        )
        self.wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY"
        )
