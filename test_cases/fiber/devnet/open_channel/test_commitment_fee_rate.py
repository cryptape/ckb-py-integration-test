import pytest

from framework.basic_fiber import FiberTest


class TestCommitmentFeeRate(FiberTest):

    def test_commitment_fee_rate_very_big(self):
        """
        commitment_fee_rate == int.max
        Returns:

            TODO : 思考commit ment fee 的测试用例
        """

        with pytest.raises(Exception) as exc_info:
            temporary_channel_id = self.fiber1.get_client().open_channel(
                {
                    "peer_id": self.fiber2.get_peer_id(),
                    "funding_amount": hex(200 * 100000000),
                    "public": True,
                    "commitment_fee_rate": hex(18446744073709551615),
                    # "tlc_fee_proportional_millionths": "0x4B0",
                }
            )
        expected_error_message = "expect more CKB amount as reserved ckb amount"
        assert expected_error_message in exc_info.value.args[0], (
            f"Expected substring '{expected_error_message}' "
            f"not found in actual string '{exc_info.value.args[0]}'"
        )

    def test_commitment_fee_rate_exist(self):
        """
        commitment_fee_rate != default.value
        Returns:
        """

    def test_commitment_fee_rate_zero(self):
        """
        commitment_fee_rate == 0
        Returns:
        """
        with pytest.raises(Exception) as exc_info:
            temporary_channel_id = self.fiber1.get_client().open_channel(
                {
                    "peer_id": self.fiber2.get_peer_id(),
                    "funding_amount": hex(200 * 100000000),
                    "public": True,
                    "commitment_fee_rate": hex(0),
                    # "tlc_fee_proportional_millionths": "0x4B0",
                }
            )
        expected_error_message = "Commitment fee rate is less than 1000"
        assert expected_error_message in exc_info.value.args[0], (
            f"Expected substring '{expected_error_message}' "
            f"not found in actual string '{exc_info.value.args[0]}'"
        )

    def test_commitment_fee_rate_is_1(self):
        """
         commitment_fee_rate == 1
        Returns:
        Returns:

        """

        with pytest.raises(Exception) as exc_info:
            temporary_channel_id = self.fiber1.get_client().open_channel(
                {
                    "peer_id": self.fiber2.get_peer_id(),
                    "funding_amount": hex(200 * 100000000),
                    "public": True,
                    "commitment_fee_rate": hex(1),
                    # "tlc_fee_proportional_millionths": "0x4B0",
                }
            )
        expected_error_message = "Commitment fee rate is less than 1000"
        assert expected_error_message in exc_info.value.args[0], (
            f"Expected substring '{expected_error_message}' "
            f"not found in actual string '{exc_info.value.args[0]}'"
        )
