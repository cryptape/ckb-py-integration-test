import time

import pytest

from framework.basic_fiber import FiberTest


class TestMaxTlcValueInFlight(FiberTest):

    @pytest.mark.skip("todo")
    def test_max_tlc_value_in_flight_none(self):
        """
        max_tlc_value_in_flight = none
        Returns:
        """
        # self.test_linked_peer()

    def test_max_tlc_value_in_flight_is_zero(self):
        """
        max_tlc_value_in_flight = 0
        Returns:
        """

        self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(1000 * 100000000),
                "public": True,
                "max_tlc_value_in_flight": "0x0",
                "funding_udt_type_script": {
                    "code_hash": self.udtContract.get_code_hash(True, self.node.rpcUrl),
                    "hash_type": "type",
                    "args": self.udtContract.get_owner_arg_by_lock_arg(
                        self.account1["lock_arg"]
                    ),
                },
                # "tlc_fee_proportional_millionths": "0x4B0",
            }
        )

        time.sleep(1)
        self.wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
        )
        time.sleep(5)
        # transfer
        self.fiber1.get_client().graph_channels()
        self.fiber1.get_client().graph_nodes()
        payment_preimage = self.generate_random_preimage()
        channels = self.fiber1.get_client().list_channels({})
        invoice_balance = hex(500 * 100000000)

        invoice = self.fiber2.get_client().new_invoice(
            {
                "amount": invoice_balance,
                "currency": "Fibd",
                "description": "test invoice generated by node2",
                "expiry": "0xe10",
                "final_cltv": "0x28",
                "payment_preimage": payment_preimage,
                "hash_algorithm": "sha256",
                "udt_type_script": {
                    "code_hash": self.udtContract.get_code_hash(True, self.node.rpcUrl),
                    "hash_type": "type",
                    "args": self.udtContract.get_owner_arg_by_lock_arg(
                        self.account1["lock_arg"]
                    ),
                },
            }
        )
        with pytest.raises(Exception) as exc_info:
            self.fiber1.get_client().send_payment(
                {
                    "invoice": invoice["invoice_address"],
                }
            )
        expected_error_message = "TemporaryChannelFailure"
        assert expected_error_message in exc_info.value.args[0], (
            f"Expected substring '{expected_error_message}' "
            f"not found in actual string '{exc_info.value.args[0]}'"
        )
        #
        # invoice_balance = hex(160 * 100000000)
        # payment_preimage = self.generate_random_preimage()
        # invoice = self.fiber1.get_client().new_invoice(
        #     {
        #         "amount": invoice_balance,
        #         "currency": "Fibd",
        #         "description": "test invoice generated by node2",
        #         "expiry": "0xe10",
        #         "final_cltv": "0x28",
        #         "payment_preimage": payment_preimage,
        #         "hash_algorithm": "sha256",
        #         "udt_type_script": {
        #             "code_hash": self.udtContract.get_code_hash(True, self.node.rpcUrl),
        #             "hash_type": "type",
        #             "args": self.udtContract.get_owner_arg_by_lock_arg(
        #                 self.account1["lock_arg"]
        #             ),
        #         },
        #     }
        # )
        # before_channel = self.fiber2.get_client().list_channels({})
        # print("node2 send 1 ckb failed ")
        # with pytest.raises(Exception) as exc_info:
        #     self.fiber2.get_client().send_payment(
        #         {
        #             "invoice": invoice["invoice_address"],
        #         }
        #     )
        # expected_error_message = "no path found"
        # assert expected_error_message in exc_info.value.args[0], (
        #     f"Expected substring '{expected_error_message}' "
        #     f"not found in actual string '{exc_info.value.args[0]}'"
        # )

        channels = self.fiber1.get_client().list_channels(
            {"peer_id": self.fiber2.get_peer_id()}
        )
        N1N2_CHANNEL_ID = channels["channels"][0]["channel_id"]
        self.fiber1.get_client().graph_channels()

        before_balance1 = self.Ckb_cli.wallet_get_capacity(
            self.account1["address"]["testnet"]
        )
        before_balance2 = self.Ckb_cli.wallet_get_capacity(
            self.account2["address"]["testnet"]
        )
        # shut down
        self.fiber1.get_client().shutdown_channel(
            {
                "channel_id": N1N2_CHANNEL_ID,
                "close_script": {
                    "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
                    "hash_type": "type",
                    "args": self.account1["lock_arg"],
                },
                "fee_rate": "0x3FC",
            }
        )
        # todo wait close tx commit
        time.sleep(20)
        after_balance1 = self.Ckb_cli.wallet_get_capacity(
            self.account1["address"]["testnet"]
        )
        after_balance2 = self.Ckb_cli.wallet_get_capacity(
            self.account2["address"]["testnet"]
        )
        print("before_balance1:", before_balance1)
        print("before_balance2:", before_balance2)
        print("after_balance1:", after_balance1)
        print("after_balance2:", after_balance2)

    def test_max_tlc_value_in_flight_overflow(self):
        with pytest.raises(Exception) as exc_info:
            temporary_channel_id = self.fiber2.get_client().open_channel(
                {
                    "peer_id": self.fiber1.get_peer_id(),
                    "funding_amount": hex(1000 * 100000000),
                    "public": True,
                    # "tlc_min_value": hex(2 * 100000000)
                    # "funding_fee_rate": "0xffff",
                    "max_tlc_value_in_flight": "0x1FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF",
                }
            )
        expected_error_message = "Invalid params"
        assert expected_error_message in exc_info.value.args[0], (
            f"Expected substring '{expected_error_message}' "
            f"not found in actual string '{exc_info.value.args[0]}'"
        )

    def test_ckb_max_tlc_value_in_flight_too_min(self):
        """
        max_tlc_value_in_flight == 1
        Returns:
        """
        self.fiber1.connect_peer(self.fiber2)
        time.sleep(5)
        self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(1000 * 100000000),
                "public": True,
                "max_tlc_value_in_flight": "0x1",
                # "tlc_fee_proportional_millionths": "0x4B0",
            }
        )

        time.sleep(1)
        self.wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
        )
        time.sleep(5)
        # transfer
        self.fiber1.get_client().graph_channels()
        self.fiber1.get_client().graph_nodes()
        payment_preimage = self.generate_random_preimage()
        channels = self.fiber1.get_client().list_channels({})
        # send 0 ckb
        invoice_balance = hex(0)

        invoice = self.fiber2.get_client().new_invoice(
            {
                "amount": invoice_balance,
                "currency": "Fibd",
                "description": "test invoice generated by node2",
                "expiry": "0xe10",
                "final_cltv": "0x28",
                "payment_preimage": payment_preimage,
                "hash_algorithm": "sha256",
            }
        )
        before_channel = self.fiber1.get_client().list_channels({})

        with pytest.raises(Exception) as exc_info:
            self.fiber1.get_client().send_payment(
                {
                    "invoice": invoice["invoice_address"],
                }
            )
        expected_error_message = "Failed to build route"
        assert expected_error_message in exc_info.value.args[0], (
            f"Expected substring '{expected_error_message}' "
            f"not found in actual string '{exc_info.value.args[0]}'"
        )
        # send 0.00000001 ckb
        invoice_balance = hex(1)
        payment_preimage = self.generate_random_preimage()

        invoice = self.fiber2.get_client().new_invoice(
            {
                "amount": invoice_balance,
                "currency": "Fibd",
                "description": "test invoice generated by node2",
                "expiry": "0xe10",
                "final_cltv": "0x28",
                "payment_preimage": payment_preimage,
                "hash_algorithm": "sha256",
            }
        )
        before_channel = self.fiber1.get_client().list_channels({})

        self.fiber1.get_client().send_payment(
            {
                "invoice": invoice["invoice_address"],
            }
        )
        time.sleep(10)
        after_channel = self.fiber1.get_client().list_channels({})
        assert int(before_channel["channels"][0]["local_balance"], 16) - int(
            after_channel["channels"][0]["local_balance"], 16
        ) == int(invoice_balance, 16)

        invoice_balance = hex(1)
        payment_preimage = self.generate_random_preimage()
        invoice = self.fiber1.get_client().new_invoice(
            {
                "amount": invoice_balance,
                "currency": "Fibd",
                "description": "test invoice generated by node2",
                "expiry": "0xe10",
                "final_cltv": "0x28",
                "payment_preimage": payment_preimage,
                "hash_algorithm": "sha256",
            }
        )
        time.sleep(1)
        print("node2 send 1 ckb failed ")
        before_channel_2 = self.fiber2.get_client().list_channels({})
        self.fiber2.get_client().send_payment(
            {
                "invoice": invoice["invoice_address"],
            }
        )
        time.sleep(10)
        after_channel_2 = self.fiber2.get_client().list_channels({})
        assert int(before_channel_2["channels"][0]["local_balance"], 16) - int(
            after_channel_2["channels"][0]["local_balance"], 16
        ) == int(invoice_balance, 16)

        channels = self.fiber1.get_client().list_channels(
            {"peer_id": self.fiber2.get_peer_id()}
        )
        N1N2_CHANNEL_ID = channels["channels"][0]["channel_id"]
        self.fiber1.get_client().graph_channels()

        before_balance1 = self.Ckb_cli.wallet_get_capacity(
            self.account1["address"]["testnet"]
        )
        before_balance2 = self.Ckb_cli.wallet_get_capacity(
            self.account2["address"]["testnet"]
        )
        # shut down
        self.fiber1.get_client().shutdown_channel(
            {
                "channel_id": N1N2_CHANNEL_ID,
                "close_script": {
                    "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
                    "hash_type": "type",
                    "args": self.account1["lock_arg"],
                },
                "fee_rate": "0x3FC",
            }
        )
        # todo wait close tx commit
        time.sleep(20)
        after_balance1 = self.Ckb_cli.wallet_get_capacity(
            self.account1["address"]["testnet"]
        )
        after_balance2 = self.Ckb_cli.wallet_get_capacity(
            self.account2["address"]["testnet"]
        )
        print("before_balance1:", before_balance1)
        print("before_balance2:", before_balance2)
        print("after_balance1:", after_balance1)
        print("after_balance2:", after_balance2)
        assert after_balance2 - before_balance2 == 62

    def test_udt_max_tlc_value_in_flight_too_min(self):
        """
        max_tlc_value_in_flight == 1
        Returns:
        """
        self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(1000 * 100000000),
                "public": True,
                "max_tlc_value_in_flight": "0x1",
                "funding_udt_type_script": self.get_account_udt_script(
                    self.fiber1.account_private
                ),
                # "tlc_fee_proportional_millionths": "0x4B0",
            }
        )

        time.sleep(1)
        self.wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
        )
        time.sleep(5)
        # transfer
        self.fiber1.get_client().graph_channels()
        self.fiber1.get_client().graph_nodes()
        payment_preimage = self.generate_random_preimage()
        channels = self.fiber1.get_client().list_channels({})
        # send 0 ckb
        invoice_balance = hex(0)

        invoice = self.fiber2.get_client().new_invoice(
            {
                "amount": invoice_balance,
                "currency": "Fibd",
                "description": "test invoice generated by node2",
                "expiry": "0xe10",
                "final_cltv": "0x28",
                "payment_preimage": payment_preimage,
                "hash_algorithm": "sha256",
                "udt_type_script": self.get_account_udt_script(
                    self.fiber1.account_private
                ),
            }
        )
        before_channel = self.fiber1.get_client().list_channels({})

        with pytest.raises(Exception) as exc_info:
            self.fiber1.get_client().send_payment(
                {
                    "invoice": invoice["invoice_address"],
                }
            )
        expected_error_message = "Failed to build route"
        assert expected_error_message in exc_info.value.args[0], (
            f"Expected substring '{expected_error_message}' "
            f"not found in actual string '{exc_info.value.args[0]}'"
        )
        # send 0.00000001 ckb
        invoice_balance = hex(1)
        payment_preimage = self.generate_random_preimage()

        invoice = self.fiber2.get_client().new_invoice(
            {
                "amount": invoice_balance,
                "currency": "Fibd",
                "description": "test invoice generated by node2",
                "expiry": "0xe10",
                "final_cltv": "0x28",
                "payment_preimage": payment_preimage,
                "hash_algorithm": "sha256",
                "udt_type_script": self.get_account_udt_script(
                    self.fiber1.account_private
                ),
            }
        )
        before_channel = self.fiber1.get_client().list_channels({})

        self.fiber1.get_client().send_payment(
            {
                "invoice": invoice["invoice_address"],
            }
        )
        time.sleep(10)
        after_channel = self.fiber1.get_client().list_channels({})
        assert int(before_channel["channels"][0]["local_balance"], 16) - int(
            after_channel["channels"][0]["local_balance"], 16
        ) == int(invoice_balance, 16)

        invoice_balance = hex(1)
        payment_preimage = self.generate_random_preimage()
        invoice = self.fiber1.get_client().new_invoice(
            {
                "amount": invoice_balance,
                "currency": "Fibd",
                "description": "test invoice generated by node2",
                "expiry": "0xe10",
                "final_cltv": "0x28",
                "payment_preimage": payment_preimage,
                "hash_algorithm": "sha256",
                "udt_type_script": self.get_account_udt_script(
                    self.fiber1.account_private
                ),
            }
        )
        time.sleep(1)
        print("node2 send 1 ckb failed ")
        before_channel_2 = self.fiber2.get_client().list_channels({})
        self.fiber2.get_client().send_payment(
            {
                "invoice": invoice["invoice_address"],
            }
        )
        time.sleep(10)
        after_channel_2 = self.fiber2.get_client().list_channels({})
        assert int(before_channel_2["channels"][0]["local_balance"], 16) - int(
            after_channel_2["channels"][0]["local_balance"], 16
        ) == int(invoice_balance, 16)

        channels = self.fiber1.get_client().list_channels(
            {"peer_id": self.fiber2.get_peer_id()}
        )
        N1N2_CHANNEL_ID = channels["channels"][0]["channel_id"]
        self.fiber1.get_client().graph_channels()

        before_balance1 = self.Ckb_cli.wallet_get_capacity(
            self.account1["address"]["testnet"]
        )
        before_balance2 = self.Ckb_cli.wallet_get_capacity(
            self.account2["address"]["testnet"]
        )
        # shut down
        self.fiber1.get_client().shutdown_channel(
            {
                "channel_id": N1N2_CHANNEL_ID,
                "close_script": self.get_account_script(self.fiber1.account_private),
                "fee_rate": "0x3FC",
            }
        )
        # todo wait close tx commit
        time.sleep(20)
        after_balance1 = self.Ckb_cli.wallet_get_capacity(
            self.account1["address"]["testnet"]
        )
        after_balance2 = self.Ckb_cli.wallet_get_capacity(
            self.account2["address"]["testnet"]
        )
        print("before_balance1:", before_balance1)
        print("before_balance2:", before_balance2)
        print("after_balance1:", after_balance1)
        print("after_balance2:", after_balance2)
        assert after_balance2 - before_balance2 == 143

    def test_ckb_max_tlc_value_in_flight_not_eq_default(self):
        """
        max_tlc_value_in_flight != default
        Returns:

        """

        self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(1000 * 100000000),
                "public": True,
                "max_tlc_value_in_flight": hex(1 * 100000000),
                # "tlc_fee_proportional_millionths": "0x4B0",
            }
        )

        self.wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
        )
        time.sleep(5)
        # transfer
        self.fiber1.get_client().graph_channels()
        self.fiber1.get_client().graph_nodes()
        payment_preimage = self.generate_random_preimage()
        channels = self.fiber1.get_client().list_channels({})
        # send 1.00000001 ckb
        invoice_balance = hex(1 * 100000000 + 1)

        invoice = self.fiber2.get_client().new_invoice(
            {
                "amount": invoice_balance,
                "currency": "Fibd",
                "description": "test invoice generated by node2",
                "expiry": "0xe10",
                "final_cltv": "0x28",
                "payment_preimage": payment_preimage,
                "hash_algorithm": "sha256",
            }
        )
        before_channel = self.fiber1.get_client().list_channels({})

        with pytest.raises(Exception) as exc_info:
            self.fiber1.get_client().send_payment(
                {
                    "invoice": invoice["invoice_address"],
                }
            )
        expected_error_message = "TemporaryChannelFailure"
        assert expected_error_message in exc_info.value.args[0], (
            f"Expected substring '{expected_error_message}' "
            f"not found in actual string '{exc_info.value.args[0]}'"
        )
        # send 1  ckb
        invoice_balance = hex(1 * 100000000)
        payment_preimage = self.generate_random_preimage()

        invoice = self.fiber2.get_client().new_invoice(
            {
                "amount": invoice_balance,
                "currency": "Fibd",
                "description": "test invoice generated by node2",
                "expiry": "0xe10",
                "final_cltv": "0x28",
                "payment_preimage": payment_preimage,
                "hash_algorithm": "sha256",
            }
        )
        before_channel = self.fiber1.get_client().list_channels({})

        payment = self.fiber1.get_client().send_payment(
            {
                "invoice": invoice["invoice_address"],
            }
        )
        self.wait_payment_state(self.fiber1, payment["payment_hash"], "Success")
        after_channel = self.fiber1.get_client().list_channels({})
        assert int(before_channel["channels"][0]["local_balance"], 16) - int(
            after_channel["channels"][0]["local_balance"], 16
        ) == int(invoice_balance, 16)

        # send 1 ckb again
        invoice_balance = hex(1 * 100000000)
        payment_preimage = self.generate_random_preimage()

        invoice = self.fiber2.get_client().new_invoice(
            {
                "amount": invoice_balance,
                "currency": "Fibd",
                "description": "test invoice generated by node2",
                "expiry": "0xe10",
                "final_cltv": "0x28",
                "payment_preimage": payment_preimage,
                "hash_algorithm": "sha256",
            }
        )
        before_channel = self.fiber1.get_client().list_channels({})

        payment = self.fiber1.get_client().send_payment(
            {
                "invoice": invoice["invoice_address"],
            }
        )
        self.wait_payment_state(self.fiber1, payment["payment_hash"], "Success")
        after_channel = self.fiber1.get_client().list_channels({})
        assert int(before_channel["channels"][0]["local_balance"], 16) - int(
            after_channel["channels"][0]["local_balance"], 16
        ) == int(invoice_balance, 16)

        # node2 send 1 ckb
        invoice_balance = hex(1 * 100000000)
        payment_preimage = self.generate_random_preimage()
        invoice = self.fiber1.get_client().new_invoice(
            {
                "amount": invoice_balance,
                "currency": "Fibd",
                "description": "test invoice generated by node2",
                "expiry": "0xe10",
                "final_cltv": "0x28",
                "payment_preimage": payment_preimage,
                "hash_algorithm": "sha256",
            }
        )
        time.sleep(1)
        print("node2 send 1 ckb failed ")
        before_channel_2 = self.fiber2.get_client().list_channels({})
        self.fiber2.get_client().send_payment(
            {
                "invoice": invoice["invoice_address"],
            }
        )
        time.sleep(10)
        after_channel_2 = self.fiber2.get_client().list_channels({})
        assert int(before_channel_2["channels"][0]["local_balance"], 16) - int(
            after_channel_2["channels"][0]["local_balance"], 16
        ) == int(invoice_balance, 16)

        # node2 send 1.00000001 ckb
        invoice_balance = hex(1 * 100000000 + 1)
        payment_preimage = self.generate_random_preimage()

        invoice = self.fiber1.get_client().new_invoice(
            {
                "amount": invoice_balance,
                "currency": "Fibd",
                "description": "test invoice generated by node2",
                "expiry": "0xe10",
                "final_cltv": "0x28",
                "payment_preimage": payment_preimage,
                "hash_algorithm": "sha256",
            }
        )
        before_channel = self.fiber2.get_client().list_channels({})

        with pytest.raises(Exception) as exc_info:
            self.fiber2.get_client().send_payment(
                {
                    "invoice": invoice["invoice_address"],
                }
            )
        expected_error_message = "TemporaryChannelFailure"
        assert expected_error_message in exc_info.value.args[0], (
            f"Expected substring '{expected_error_message}' "
            f"not found in actual string '{exc_info.value.args[0]}'"
        )
        channels = self.fiber1.get_client().list_channels(
            {"peer_id": self.fiber2.get_peer_id()}
        )
        N1N2_CHANNEL_ID = channels["channels"][0]["channel_id"]
        self.fiber1.get_client().graph_channels()

        before_balance1 = self.Ckb_cli.wallet_get_capacity(
            self.account1["address"]["testnet"]
        )
        before_balance2 = self.Ckb_cli.wallet_get_capacity(
            self.account2["address"]["testnet"]
        )
        # shut down
        self.fiber1.get_client().shutdown_channel(
            {
                "channel_id": N1N2_CHANNEL_ID,
                "close_script": self.get_account_script(self.fiber1.account_private),
                "fee_rate": "0x3FC",
            }
        )
        # todo wait close tx commit
        time.sleep(20)
        after_balance1 = self.Ckb_cli.wallet_get_capacity(
            self.account1["address"]["testnet"]
        )
        after_balance2 = self.Ckb_cli.wallet_get_capacity(
            self.account2["address"]["testnet"]
        )
        print("before_balance1:", before_balance1)
        print("before_balance2:", before_balance2)
        print("after_balance1:", after_balance1)
        print("after_balance2:", after_balance2)
        assert after_balance2 - before_balance2 == 63

    def test_udt_max_tlc_value_in_flight_not_eq_default(self):
        """
        max_tlc_value_in_flight != default
        Returns:
        """

        self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(1000 * 100000000),
                "public": True,
                "max_tlc_value_in_flight": hex(1 * 100000000),
                "funding_udt_type_script": self.get_account_udt_script(
                    self.fiber1.account_private
                ),
                # "tlc_fee_proportional_millionths": "0x4B0",
            }
        )

        time.sleep(1)
        self.wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
        )
        time.sleep(5)
        # transfer
        self.fiber1.get_client().graph_channels()
        self.fiber1.get_client().graph_nodes()
        payment_preimage = self.generate_random_preimage()
        channels = self.fiber1.get_client().list_channels({})
        # send 1.00000001 ckb
        invoice_balance = hex(1 * 100000000 + 1)

        invoice = self.fiber2.get_client().new_invoice(
            {
                "amount": invoice_balance,
                "currency": "Fibd",
                "description": "test invoice generated by node2",
                "expiry": "0xe10",
                "final_cltv": "0x28",
                "payment_preimage": payment_preimage,
                "hash_algorithm": "sha256",
                "udt_type_script": self.get_account_udt_script(
                    self.fiber1.account_private
                ),
            }
        )
        before_channel = self.fiber1.get_client().list_channels({})

        with pytest.raises(Exception) as exc_info:
            self.fiber1.get_client().send_payment(
                {
                    "invoice": invoice["invoice_address"],
                }
            )
        expected_error_message = "TemporaryChannelFailure"
        assert expected_error_message in exc_info.value.args[0], (
            f"Expected substring '{expected_error_message}' "
            f"not found in actual string '{exc_info.value.args[0]}'"
        )
        # send 1  ckb
        invoice_balance = hex(1 * 100000000)
        payment_preimage = self.generate_random_preimage()

        invoice = self.fiber2.get_client().new_invoice(
            {
                "amount": invoice_balance,
                "currency": "Fibd",
                "description": "test invoice generated by node2",
                "expiry": "0xe10",
                "final_cltv": "0x28",
                "payment_preimage": payment_preimage,
                "hash_algorithm": "sha256",
                "udt_type_script": self.get_account_udt_script(
                    self.fiber1.account_private
                ),
            }
        )
        before_channel = self.fiber1.get_client().list_channels({})

        self.fiber1.get_client().send_payment(
            {
                "invoice": invoice["invoice_address"],
            }
        )
        time.sleep(10)
        after_channel = self.fiber1.get_client().list_channels({})
        assert int(before_channel["channels"][0]["local_balance"], 16) - int(
            after_channel["channels"][0]["local_balance"], 16
        ) == int(invoice_balance, 16)

        # send 1 ckb again
        invoice_balance = hex(1 * 100000000)
        payment_preimage = self.generate_random_preimage()

        invoice = self.fiber2.get_client().new_invoice(
            {
                "amount": invoice_balance,
                "currency": "Fibd",
                "description": "test invoice generated by node2",
                "expiry": "0xe10",
                "final_cltv": "0x28",
                "payment_preimage": payment_preimage,
                "hash_algorithm": "sha256",
                "udt_type_script": self.get_account_udt_script(
                    self.fiber1.account_private
                ),
            }
        )
        before_channel = self.fiber1.get_client().list_channels({})

        self.fiber1.get_client().send_payment(
            {
                "invoice": invoice["invoice_address"],
            }
        )
        time.sleep(10)
        after_channel = self.fiber1.get_client().list_channels({})
        assert int(before_channel["channels"][0]["local_balance"], 16) - int(
            after_channel["channels"][0]["local_balance"], 16
        ) == int(invoice_balance, 16)

        # node2 send 1 ckb
        invoice_balance = hex(1 * 100000000)
        payment_preimage = self.generate_random_preimage()
        invoice = self.fiber1.get_client().new_invoice(
            {
                "amount": invoice_balance,
                "currency": "Fibd",
                "description": "test invoice generated by node2",
                "expiry": "0xe10",
                "final_cltv": "0x28",
                "payment_preimage": payment_preimage,
                "hash_algorithm": "sha256",
                "udt_type_script": self.get_account_udt_script(
                    self.fiber1.account_private
                ),
            }
        )
        time.sleep(1)
        print("node2 send 1 ckb failed ")
        before_channel_2 = self.fiber2.get_client().list_channels({})
        self.fiber2.get_client().send_payment(
            {
                "invoice": invoice["invoice_address"],
            }
        )
        time.sleep(10)
        after_channel_2 = self.fiber2.get_client().list_channels({})
        assert int(before_channel_2["channels"][0]["local_balance"], 16) - int(
            after_channel_2["channels"][0]["local_balance"], 16
        ) == int(invoice_balance, 16)

        # node2 send 1.00000001 ckb
        invoice_balance = hex(1 * 100000000 + 1)
        payment_preimage = self.generate_random_preimage()

        invoice = self.fiber1.get_client().new_invoice(
            {
                "amount": invoice_balance,
                "currency": "Fibd",
                "description": "test invoice generated by node2",
                "expiry": "0xe10",
                "final_cltv": "0x28",
                "payment_preimage": payment_preimage,
                "hash_algorithm": "sha256",
                "udt_type_script": self.get_account_udt_script(
                    self.fiber1.account_private
                ),
            }
        )
        before_channel = self.fiber2.get_client().list_channels({})

        with pytest.raises(Exception) as exc_info:
            self.fiber2.get_client().send_payment(
                {
                    "invoice": invoice["invoice_address"],
                }
            )
        expected_error_message = "TemporaryChannelFailure"
        assert expected_error_message in exc_info.value.args[0], (
            f"Expected substring '{expected_error_message}' "
            f"not found in actual string '{exc_info.value.args[0]}'"
        )
        channels = self.fiber1.get_client().list_channels(
            {"peer_id": self.fiber2.get_peer_id()}
        )
        N1N2_CHANNEL_ID = channels["channels"][0]["channel_id"]
        self.fiber1.get_client().graph_channels()

        before_balance1 = self.Ckb_cli.wallet_get_capacity(
            self.account1["address"]["testnet"]
        )
        before_balance2 = self.Ckb_cli.wallet_get_capacity(
            self.account2["address"]["testnet"]
        )
        # shut down
        self.fiber1.get_client().shutdown_channel(
            {
                "channel_id": N1N2_CHANNEL_ID,
                "close_script": self.get_account_script(self.fiber1.account_private),
                "fee_rate": "0x3FC",
            }
        )
        # todo wait close tx commit
        time.sleep(20)
        after_balance1 = self.Ckb_cli.wallet_get_capacity(
            self.account1["address"]["testnet"]
        )
        after_balance2 = self.Ckb_cli.wallet_get_capacity(
            self.account2["address"]["testnet"]
        )
        print("before_balance1:", before_balance1)
        print("before_balance2:", before_balance2)
        print("after_balance1:", after_balance1)
        print("after_balance2:", after_balance2)
        assert after_balance2 - before_balance2 == 143
        account2_balance = self.udtContract.list_cell(
            self.node.getClient(),
            own_arg=self.account1["lock_arg"],
            query_arg=self.account2["lock_arg"],
        )
        account1_balance = self.udtContract.list_cell(
            self.node.getClient(),
            own_arg=self.account1["lock_arg"],
            query_arg=self.account1["lock_arg"],
        )
        print("account1:", account1_balance)
        print("account2:", account2_balance)
        assert account1_balance[-1]["balance"] == 99900000000
        assert account2_balance[-1]["balance"] == 100000000