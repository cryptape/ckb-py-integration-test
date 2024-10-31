import time

import pytest

from framework.basic_fiber import FiberTest


class TestTemporaryChannelId(FiberTest):
    # FiberTest.debug = True

    def test_temporary_channel_id_not_exist(self):
        """
        Returns:
        """

        with pytest.raises(Exception) as exc_info:
            self.fiber2.get_client().accept_channel(
                {
                    "temporary_channel_id": "0x119fb7f26b72664b5cdfec9269591a6af1c9f111f47534b7bc7993413701599a",
                    "funding_amount": hex(100 * 100000000),
                }
            )

        expected_error_message = "No channel with temp id"
        assert expected_error_message in exc_info.value.args[0], (
            f"Expected substring '{expected_error_message}' "
            f"not found in actual string '{exc_info.value.args[0]}'"
        )

    def test_temporary_channel_id_again(self):
        """
        Returns:
        """
        node_info = self.fiber1.get_client().node_info()
        open_channel_auto_accept_min_ckb_funding_amount = node_info[
            "open_channel_auto_accept_min_ckb_funding_amount"
        ]

        temporary_channel = self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(
                    int(open_channel_auto_accept_min_ckb_funding_amount, 16) - 1
                ),
                "public": True,
            }
        )
        time.sleep(1)
        self.fiber2.get_client().accept_channel(
            {
                "temporary_channel_id": temporary_channel["temporary_channel_id"],
                "funding_amount": hex(63 * 100000000),
            }
        )

        with pytest.raises(Exception) as exc_info:
            self.fiber2.get_client().accept_channel(
                {
                    "temporary_channel_id": temporary_channel["temporary_channel_id"],
                    "funding_amount": hex(64 * 100000000),
                }
            )

        expected_error_message = "No channel with temp id Hash256"
        assert expected_error_message in exc_info.value.args[0], (
            f"Expected substring '{expected_error_message}' "
            f"not found in actual string '{exc_info.value.args[0]}'"
        )

    @pytest.mark.skip("repeat")
    def test_ckb_temporary_channel_id_exist(self):
        """
        channel is ckb
        Returns:
        """
        # test_funding_amount.test_ckb_funding_amount_eq_auto_accept_channel_ckb_funding_amount

    @pytest.mark.skip("repeat")
    def test_udt_temporary_channel_id_exist(self):
        """
        channel is udt
        Returns:
        """
        # test_funding_amount.test_udt_funding_amount_zero
