import time

import pytest

from framework.basic_fiber import FiberTest


class FundingAmount(FiberTest):
    FiberTest.debug = True

    def test_funding_amount_ckb_is_zero(self):
        """
        1. funding_udt_type_script is None ,funding_amount = 0
        Returns:
        """
        with pytest.raises(Exception) as exc_info:
            temporary_channel_id = self.fiber1.get_client().open_channel(
                {
                    "peer_id": self.fiber2.get_peer_id(),
                    "funding_amount": hex(0),
                    "public": True,
                    # "tlc_fee_proportional_millionths": "0x4B0",
                }
            )
        expected_error_message = (
            "The funding amount should be greater than the reserved amount: 6200000000"
        )
        assert expected_error_message in exc_info.value.args[0], (
            f"Expected substring '{expected_error_message}' "
            f"not found in actual string '{exc_info.value.args[0]}'"
        )

    def test_funding_amount_ckb_lt_62(self):
        """
        1. funding_udt_type_script is None ,funding_amount < 62
        Returns:
        """
        """
                1. funding_udt_type_script is None ,funding_amount = 0
                Returns:
                """
        with pytest.raises(Exception) as exc_info:
            temporary_channel_id = self.fiber1.get_client().open_channel(
                {
                    "peer_id": self.fiber2.get_peer_id(),
                    "funding_amount": hex(62 * 100000000 - 1),
                    "public": True,
                    # "tlc_fee_proportional_millionths": "0x4B0",
                }
            )
        expected_error_message = (
            "The funding amount should be greater than the reserved amount"
        )
        assert expected_error_message in exc_info.value.args[0], (
            f"Expected substring '{expected_error_message}' "
            f"not found in actual string '{exc_info.value.args[0]}'"
        )

    def test_funding_amount_ckb_0xfffffffffffffffffffffffffffffff(self):
        """
        1. funding_udt_type_script is None ,funding_amount > account balance
        Returns:
        0xfffffffffffffffffffffffffffffff
        """

        capacity = self.Ckb_cli.wallet_get_capacity(self.account2["address"]["testnet"])
        with pytest.raises(Exception) as exc_info:
            temporary_channel_id = self.fiber1.get_client().open_channel(
                {
                    "peer_id": self.fiber2.get_peer_id(),
                    "funding_amount": "0xfffffffffffffffffffffffffffffff",
                    "public": True,
                    # "tlc_fee_proportional_millionths": "0x4B0",
                }
            )
        expected_error_message = (
            "The funding amount should be less than 18446744073709551615"
        )
        assert expected_error_message in exc_info.value.args[0], (
            f"Expected substring '{expected_error_message}' "
            f"not found in actual string '{exc_info.value.args[0]}'"
        )

    def test_funding_amount_ckb_gt_account_balance(self):
        """
        1. funding_udt_type_script is None ,funding_amount > account balance
        Returns:
            status : NEGOTIATING_FUNDING
        """

        capacity = self.Ckb_cli.wallet_get_capacity(self.account2["address"]["testnet"])
        temporary_channel_id = self.fiber2.get_client().open_channel(
            {
                "peer_id": self.fiber1.get_peer_id(),
                "funding_amount": hex(int(capacity) * 100000000 * 2),
                "public": True,
                # "tlc_fee_proportional_millionths": "0x4B0",
            }
        )
        self.wait_for_channel_state(
            self.fiber2.get_client(),
            self.fiber1.get_peer_id(),
            "NEGOTIATING_FUNDING",
            120,
        )

    def test_funding_amount_ckb_eq_account_balance(self):
        """
        1. funding_udt_type_script is None ,funding_amount == account balance
        Returns:
        """
        capacity = self.Ckb_cli.wallet_get_capacity(self.account2["address"]["testnet"])
        temporary_channel_id = self.fiber2.get_client().open_channel(
            {
                "peer_id": self.fiber1.get_peer_id(),
                "funding_amount": hex(int(capacity) * 100000000),
                "public": True,
                # "tlc_fee_proportional_millionths": "0x4B0",
            }
        )
        self.wait_for_channel_state(
            self.fiber2.get_client(),
            self.fiber1.get_peer_id(),
            "NEGOTIATING_FUNDING",
            120,
        )

    def test_funding_amount_ckb_lt_account_balance(self):
        """
        1. funding_udt_type_script is None ,funding_amount < account balance
        Returns:
        """
        pass
        # self.test_linked_peer()

    def test_funding_amount_gt_int_max(self):
        """
        funding_amount > int.max
        Args:
            self:
        Returns:
        """

        #  The funding amount should be less than 18446744073709551615
        with pytest.raises(Exception) as exc_info:
            temporary_channel_id = self.fiber1.get_client().open_channel(
                {
                    "peer_id": self.fiber2.get_peer_id(),
                    "funding_amount": hex(18446744073709551616),
                    "public": True,
                    # "tlc_fee_proportional_millionths": "0x4B0",
                }
            )
        expected_error_message = (
            "The funding amount should be less than 18446744073709551615"
        )
        assert expected_error_message in exc_info.value.args[0], (
            f"Expected substring '{expected_error_message}' "
            f"not found in actual string '{exc_info.value.args[0]}'"
        )
