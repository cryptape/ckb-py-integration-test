import time

import pytest

from framework.basic_fiber import FiberTest


class TestAllowSelfPaymnent(FiberTest):
    # FiberTest.debug = True
    def test_a1_to_b1_to_a1(self):
        """
        a1-b1-a1
            a1->b1(0)
               key send: no path found
               invoice send : no path found
            a1->b1( 不为 0)
                key send: no path found
               invoice send : no path found
        Returns:

        """
        # open channel a1-b1
        self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(1000 * 100000000),
                "public": True,
            }
        )
        self.wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY"
        )
        time.sleep(1)
        # allow_self_payment is none
        with pytest.raises(Exception) as exc_info:
            payment1 = self.fiber1.get_client().send_payment(
                {
                    "target_pubkey": self.fiber1.get_client().node_info()["node_id"],
                    "amount": hex(500 * 10000000),
                    "keysend": True,
                    "dry_run": True,
                }
            )
        expected_error_message = "allow_self_payment is not enable"
        assert expected_error_message in exc_info.value.args[0], (
            f"Expected substring '{expected_error_message}' "
            f"not found in actual string '{exc_info.value.args[0]}'"
        )
        with pytest.raises(Exception) as exc_info:
            invoice = self.fiber1.get_client().new_invoice(
                {
                    "amount": hex(100 * 10000000),
                    "currency": "Fibd",
                    "description": "test invoice generated by node1",
                    "expiry": "0xe10",
                    "final_cltv": "0x28",
                    "payment_preimage": self.generate_random_preimage(),
                }
            )
            payment1 = self.fiber1.get_client().send_payment(
                {
                    "invoice": invoice["invoice_address"],
                }
            )
        expected_error_message = "allow_self_payment is not enable"
        assert expected_error_message in exc_info.value.args[0], (
            f"Expected substring '{expected_error_message}' "
            f"not found in actual string '{exc_info.value.args[0]}'"
        )

        # a1(100000000 )->b1(0)  a1 send payment with self pay
        with pytest.raises(Exception) as exc_info:
            payment1 = self.fiber1.get_client().send_payment(
                {
                    "target_pubkey": self.fiber1.get_client().node_info()["node_id"],
                    "amount": hex(500 * 10000000),
                    "keysend": True,
                    "dry_run": True,
                    "allow_self_payment": True,
                }
            )
        expected_error_message = "Failed to build route"
        assert expected_error_message in exc_info.value.args[0], (
            f"Expected substring '{expected_error_message}' "
            f"not found in actual string '{exc_info.value.args[0]}'"
        )
        with pytest.raises(Exception) as exc_info:
            invoice = self.fiber1.get_client().new_invoice(
                {
                    "amount": hex(100 * 10000000),
                    "currency": "Fibd",
                    "description": "test invoice generated by node1",
                    "expiry": "0xe10",
                    "final_cltv": "0x28",
                    "payment_preimage": self.generate_random_preimage(),
                }
            )
            payment1 = self.fiber1.get_client().send_payment(
                {"invoice": invoice["invoice_address"], "allow_self_payment": True}
            )
        expected_error_message = "Failed to build route"
        assert expected_error_message in exc_info.value.args[0], (
            f"Expected substring '{expected_error_message}' "
            f"not found in actual string '{exc_info.value.args[0]}'"
        )
        # a1(1000 )->b1(100)  a1 send payment with self pay
        payment1 = self.fiber1.get_client().send_payment(
            {
                "target_pubkey": self.fiber2.get_client().node_info()["node_id"],
                "amount": hex(100 * 10000000),
                "keysend": True,
            }
        )
        self.wait_payment_state(self.fiber1, payment1["payment_hash"], "Success")
        channels = self.fiber2.get_client().list_channels({})
        assert channels["channels"][0]["local_balance"] == hex(100 * 10000000)
        with pytest.raises(Exception) as exc_info:
            payment1 = self.fiber1.get_client().send_payment(
                {
                    "target_pubkey": self.fiber1.get_client().node_info()["node_id"],
                    "amount": hex(10 * 10000000),
                    "keysend": True,
                    "dry_run": True,
                    "allow_self_payment": True,
                }
            )
        expected_error_message = "Failed to build route"
        assert expected_error_message in exc_info.value.args[0], (
            f"Expected substring '{expected_error_message}' "
            f"not found in actual string '{exc_info.value.args[0]}'"
        )
        with pytest.raises(Exception) as exc_info:
            invoice = self.fiber1.get_client().new_invoice(
                {
                    "amount": hex(10 * 10000000),
                    "currency": "Fibd",
                    "description": "test invoice generated by node1",
                    "expiry": "0xe10",
                    "final_cltv": "0x28",
                    "payment_preimage": self.generate_random_preimage(),
                }
            )
            payment1 = self.fiber1.get_client().send_payment(
                {"invoice": invoice["invoice_address"], "allow_self_payment": True}
            )
        expected_error_message = "Failed to build route"
        assert expected_error_message in exc_info.value.args[0], (
            f"Expected substring '{expected_error_message}' "
            f"not found in actual string '{exc_info.value.args[0]}'"
        )

    # @pytest.mark.skip("https://github.com/nervosnetwork/fiber/issues/355")
    def test_a1_to_b1_to_a2(self):
        """
        a1(1000)-b1(0) a2(0)-b2(1000)
            1. dry_run
            2. key_send
            3. invoice send

        todo a1(900)-b1(100) a2(100)-b2(900)
            1. dry_run
            2. key_send
            3. invoice send

        Returns:

        """
        # open channel a1-b1
        self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(1000 * 100000000),
                "public": True,
            }
        )
        self.wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY"
        )
        self.wait_for_channel_state(
            self.fiber2.get_client(), self.fiber1.get_peer_id(), "CHANNEL_READY"
        )
        self.fiber2.get_client().open_channel(
            {
                "peer_id": self.fiber1.get_peer_id(),
                "funding_amount": hex(1000 * 100000000),
                "public": True,
            }
        )
        time.sleep(2)
        self.wait_for_channel_state(
            self.fiber2.get_client(), self.fiber1.get_peer_id(), "CHANNEL_READY"
        )
        time.sleep(1)

        # allow_self_payment is none
        with pytest.raises(Exception) as exc_info:
            payment1 = self.fiber1.get_client().send_payment(
                {
                    "target_pubkey": self.fiber1.get_client().node_info()["node_id"],
                    "amount": hex(500 * 10000000),
                    "keysend": True,
                    "dry_run": True,
                }
            )
        expected_error_message = "allow_self_payment is not enable"
        assert expected_error_message in exc_info.value.args[0], (
            f"Expected substring '{expected_error_message}' "
            f"not found in actual string '{exc_info.value.args[0]}'"
        )
        with pytest.raises(Exception) as exc_info:
            invoice = self.fiber1.get_client().new_invoice(
                {
                    "amount": hex(100 * 10000000),
                    "currency": "Fibd",
                    "description": "test invoice generated by node1",
                    "expiry": "0xe10",
                    "final_cltv": "0x28",
                    "payment_preimage": self.generate_random_preimage(),
                }
            )
            payment1 = self.fiber1.get_client().send_payment(
                {
                    "invoice": invoice["invoice_address"],
                }
            )
        expected_error_message = "allow_self_payment is not enable"
        assert expected_error_message in exc_info.value.args[0], (
            f"Expected substring '{expected_error_message}' "
            f"not found in actual string '{exc_info.value.args[0]}'"
        )

        # a1(100000000 )->b1(0)  a1 send payment with self pay
        payment1 = self.fiber1.get_client().send_payment(
            {
                "target_pubkey": self.fiber1.get_client().node_info()["node_id"],
                "amount": hex(500 * 10000000),
                "keysend": True,
                "dry_run": True,
                "allow_self_payment": True,
            }
        )
        assert payment1["fee"] != "0x0"
        invoice = self.fiber1.get_client().new_invoice(
            {
                "amount": hex(100 * 10000000),
                "currency": "Fibd",
                "description": "test invoice generated by node1",
                "expiry": "0xe10",
                "final_cltv": "0x28",
                "payment_preimage": self.generate_random_preimage(),
            }
        )
        payment1 = self.fiber1.get_client().send_payment(
            {"invoice": invoice["invoice_address"], "allow_self_payment": True}
        )
        self.wait_payment_state(self.fiber1, payment1["payment_hash"], "Success")
        # todo check channel balance
        # todo a1(1000 )->b1(100)  a1 send payment with self pay

    # @pytest.mark.skip("https://github.com/nervosnetwork/fiber/issues/362")
    @pytest.mark.skip("wait ")
    def test_a1_to_b1_to_c1_a2(self):
        """

        Returns:

        """
        self.fiber3 = self.start_new_fiber(self.generate_account(10000))
        self.fiber3.connect_peer(self.fiber2)
        self.fiber3.connect_peer(self.fiber1)
        self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(1000 * 100000000),
                "public": True,
            }
        )
        self.wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY"
        )
        self.fiber2.get_client().open_channel(
            {
                "peer_id": self.fiber3.get_peer_id(),
                "funding_amount": hex(1000 * 100000000),
                "public": True,
            }
        )
        self.wait_for_channel_state(
            self.fiber2.get_client(), self.fiber3.get_peer_id(), "CHANNEL_READY"
        )
        self.wait_for_channel_state(
            self.fiber3.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY"
        )
        self.fiber3.get_client().open_channel(
            {
                "peer_id": self.fiber1.get_peer_id(),
                "funding_amount": hex(1000 * 100000000),
                "public": True,
            }
        )
        self.wait_for_channel_state(
            self.fiber3.get_client(), self.fiber1.get_peer_id(), "CHANNEL_READY"
        )
        # node1 send to self
        time.sleep(1)
        for i in range(3):
            payment1 = self.fiber1.get_client().send_payment(
                {
                    "target_pubkey": self.fiber1.get_client().node_info()["node_id"],
                    "amount": hex(6 * 10000000),
                    "keysend": True,
                    "allow_self_payment": True,
                }
            )
            self.wait_payment_state(self.fiber1, payment1["payment_hash"], "Success")
        # after fix todo add check

    def test_a1_to_b1_to_c1_a2_2(self):
        """

        Returns:

        """
        self.fiber3 = self.start_new_fiber(self.generate_account(10000))
        self.fiber3.connect_peer(self.fiber2)
        self.fiber3.connect_peer(self.fiber1)
        self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(1000 * 100000000),
                "public": True,
            }
        )
        self.wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY"
        )
        self.fiber2.get_client().open_channel(
            {
                "peer_id": self.fiber3.get_peer_id(),
                "funding_amount": hex(1000 * 100000000),
                "public": True,
            }
        )
        self.wait_for_channel_state(
            self.fiber2.get_client(), self.fiber3.get_peer_id(), "CHANNEL_READY"
        )
        self.wait_for_channel_state(
            self.fiber3.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY"
        )
        self.fiber3.get_client().open_channel(
            {
                "peer_id": self.fiber1.get_peer_id(),
                "funding_amount": hex(1000 * 100000000),
                "public": True,
            }
        )
        self.wait_for_channel_state(
            self.fiber3.get_client(), self.fiber1.get_peer_id(), "CHANNEL_READY"
        )
        # node1 send to self
        time.sleep(1)
        payment1 = self.fiber1.get_client().send_payment(
            {
                "target_pubkey": self.fiber1.get_client().node_info()["node_id"],
                "amount": hex(6 * 10000000),
                "keysend": True,
                "allow_self_payment": True,
            }
        )
        self.wait_payment_state(self.fiber1, payment1["payment_hash"], "Success")
        # after fix todo add check