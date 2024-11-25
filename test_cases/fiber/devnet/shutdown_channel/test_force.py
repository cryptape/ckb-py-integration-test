import time

import pytest

from framework.basic_fiber import FiberTest


class TestForce(FiberTest):
    """
    - 对方节点在线
    - 对方节点不在线
    - channel状态
        - pending
        - ready
        - xxx
    """

    # FiberTest.debug = True

    @pytest.mark.skip("https://github.com/nervosnetwork/fiber/issues/333")
    def test_node_offline(self):
        temporary_channel_id = self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(200 * 100000000),
                "public": False,
                # "tlc_fee_proportional_millionths": "0x4B0",
            }
        )
        time.sleep(1)
        self.wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
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
        self.fiber2.stop()
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
                "force": True,
            }
        )
        time.sleep(20)
        node_info = self.fiber1.get_client().node_info()
        print("node info :", node_info)
        assert node_info["channel_count"] == "0x0"
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
        assert after_balance2 - before_balance2 == 62.0
        # todo  添加更多断言

    def test_node_online(self):
        temporary_channel_id = self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(200 * 100000000),
                "public": False,
                # "tlc_fee_proportional_millionths": "0x4B0",
            }
        )
        time.sleep(1)
        self.wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
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
                "close_script": {
                    "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
                    "hash_type": "type",
                    "args": self.account1["lock_arg"],
                },
                "fee_rate": "0x3FC",
                "force": True,
            }
        )
        time.sleep(20)
        # todo check fiber2
        # todo check graph_channels
        # todo check list channel

    def test_NegotiatingFunding(self):
        pass

    def test_CollaboratingFundingTx(self):
        pass

    def test_SigningCommitment(self):
        pass

    def test_AwaitingTxSignatures(self):
        temporary_channel_id = self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(200 * 100000000),
                "public": False,
                # "tlc_fee_proportional_millionths": "0x4B0",
            }
        )
        time.sleep(1)
        self.wait_for_channel_state(
            self.fiber1.get_client(),
            self.fiber2.get_peer_id(),
            "AWAITING_TX_SIGNATURES",
            120,
        )
        channels = self.fiber1.get_client().list_channels(
            {"peer_id": self.fiber2.get_peer_id()}
        )
        N1N2_CHANNEL_ID = channels["channels"][0]["channel_id"]

        with pytest.raises(Exception) as exc_info:
            self.fiber1.get_client().shutdown_channel(
                {
                    "channel_id": N1N2_CHANNEL_ID,
                    "close_script": {
                        "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
                        "hash_type": "type",
                        "args": self.account1["lock_arg"],
                    },
                    "fee_rate": "0x3FC",
                    "force": True,
                }
            )
        expected_error_message = "Handling force shutdown command invalid state"
        assert expected_error_message in exc_info.value.args[0], (
            f"Expected substring '{expected_error_message}' "
            f"not found in actual string '{exc_info.value.args[0]}'"
        )

    @pytest.mark.skip("抓不到这个状态")
    def test_AwaitingChannelReady(self):
        """
        todo not found state
        Returns:

        """
        temporary_channel_id = self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(200 * 100000000),
                "public": False,
                # "tlc_fee_proportional_millionths": "0x4B0",
            }
        )
        time.sleep(1)
        self.wait_for_channel_state(
            self.fiber1.get_client(),
            self.fiber2.get_peer_id(),
            "AWAITING_CHANNEL_READY",
            120,
        )
        channels = self.fiber1.get_client().list_channels(
            {"peer_id": self.fiber2.get_peer_id()}
        )
        N1N2_CHANNEL_ID = channels["channels"][0]["channel_id"]

        with pytest.raises(Exception) as exc_info:
            self.fiber1.get_client().shutdown_channel(
                {
                    "channel_id": N1N2_CHANNEL_ID,
                    "close_script": {
                        "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
                        "hash_type": "type",
                        "args": self.account1["lock_arg"],
                    },
                    "fee_rate": "0x3FC",
                    "force": True,
                }
            )
        expected_error_message = "Handling force shutdown command invalid state"
        assert expected_error_message in exc_info.value.args[0], (
            f"Expected substring '{expected_error_message}' "
            f"not found in actual string '{exc_info.value.args[0]}'"
        )

    @pytest.mark.skip("repeat")
    def test_ChannelReady(self):
        pass

    @pytest.mark.skip("have bug")
    def test_in_tx(self):
        temporary_channel_id = self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(200 * 100000000),
                "public": True,
                # "tlc_fee_proportional_millionths": "0x4B0",
            }
        )
        time.sleep(1)
        self.wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
        )

        amount = 1
        invoice = self.fiber2.get_client().new_invoice(
            {
                "amount": hex(amount),
                "currency": "Fibd",
                "description": "test invoice generated by node2",
                "expiry": "0xe10",
                "final_cltv": "0x28",
                "payment_preimage": self.generate_random_preimage(),
                "hash_algorithm": "sha256",
            }
        )
        time.sleep(1)

        channels = self.fiber1.get_client().list_channels(
            {"peer_id": self.fiber2.get_peer_id()}
        )
        N1N2_CHANNEL_ID = channels["channels"][0]["channel_id"]

        # 5. Send payment using the created invoice
        payment = self.fiber1.get_client().send_payment(
            {
                "invoice": invoice["invoice_address"],
            }
        )
        self.fiber1.get_client().shutdown_channel(
            {
                "channel_id": N1N2_CHANNEL_ID,
                "close_script": {
                    "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
                    "hash_type": "type",
                    "args": self.account1["lock_arg"],
                },
                "fee_rate": "0x3FC",
                "force": True,
            }
        )
        self.fiber1.get_client().get_payment({"payment_hash": payment["payment_hash"]})

        # self.wait_for_channel_state(self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120)

    @pytest.mark.skip("https://github.com/nervosnetwork/fiber/issues/333")
    def test_in_tx_offline(self):
        temporary_channel_id = self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(200 * 100000000),
                "public": True,
                # "tlc_fee_proportional_millionths": "0x4B0",
            }
        )
        time.sleep(1)
        self.wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
        )

        amount = 1
        invoice = self.fiber2.get_client().new_invoice(
            {
                "amount": hex(amount),
                "currency": "Fibd",
                "description": "test invoice generated by node2",
                "expiry": "0xe10",
                "final_cltv": "0x28",
                "payment_preimage": self.generate_random_preimage(),
                "hash_algorithm": "sha256",
            }
        )
        time.sleep(1)

        channels = self.fiber1.get_client().list_channels(
            {"peer_id": self.fiber2.get_peer_id()}
        )
        N1N2_CHANNEL_ID = channels["channels"][0]["channel_id"]

        # 5. Send payment using the created invoice
        self.fiber2.get_client().shutdown_channel(
            {
                "channel_id": N1N2_CHANNEL_ID,
                "close_script": {
                    "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
                    "hash_type": "type",
                    "args": self.account2["lock_arg"],
                },
                "fee_rate": "0x3FC",
                "force": True,
            }
        )

        payment = self.fiber1.get_client().send_payment(
            {
                "invoice": invoice["invoice_address"],
            }
        )

        self.wait_payment_state(self.fiber1, payment["payment_hash"], "Success")

    def test_ShuttingDown(self):
        temporary_channel_id = self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(200 * 100000000),
                "public": True,
                # "tlc_fee_proportional_millionths": "0x4B0",
            }
        )
        time.sleep(1)
        self.wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
        )

        amount = 1
        invoice = self.fiber2.get_client().new_invoice(
            {
                "amount": hex(amount),
                "currency": "Fibd",
                "description": "test invoice generated by node2",
                "expiry": "0xe10",
                "final_cltv": "0x28",
                "payment_preimage": self.generate_random_preimage(),
                "hash_algorithm": "sha256",
            }
        )
        time.sleep(1)

        channels = self.fiber1.get_client().list_channels(
            {"peer_id": self.fiber2.get_peer_id()}
        )
        N1N2_CHANNEL_ID = channels["channels"][0]["channel_id"]

        # 5. Send payment using the created invoice
        self.fiber1.get_client().shutdown_channel(
            {
                "channel_id": N1N2_CHANNEL_ID,
                "close_script": {
                    "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
                    "hash_type": "type",
                    "args": self.account2["lock_arg"],
                },
                "fee_rate": "0x3FC",
                # "force": True
            }
        )
        self.fiber2.get_client().shutdown_channel(
            {
                "channel_id": N1N2_CHANNEL_ID,
                "close_script": {
                    "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
                    "hash_type": "type",
                    "args": self.account2["lock_arg"],
                },
                "fee_rate": "0x3FC",
                "force": True,
            }
        )
        # todo add check

    def test_force_ckb(self):
        temporary_channel_id = self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(200 * 100000000),
                "public": True,
                # "tlc_fee_proportional_millionths": "0x4B0",
            }
        )
        time.sleep(1)
        self.wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
        )
        time.sleep(1)

        invoice_balance = hex(50 * 100000000)

        invoice = self.fiber2.get_client().new_invoice(
            {
                "amount": invoice_balance,
                "currency": "Fibd",
                "description": "test invoice generated by node2",
                "expiry": "0xe10",
                "final_cltv": "0x28",
                "payment_preimage": self.generate_random_preimage(),
                "hash_algorithm": "sha256",
            }
        )
        before_channel = self.fiber1.get_client().list_channels({})
        time.sleep(1)
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
        channels = self.fiber1.get_client().list_channels(
            {"peer_id": self.fiber2.get_peer_id()}
        )
        N1N2_CHANNEL_ID = channels["channels"][0]["channel_id"]

        # before_balance2 = self.Ckb_cli.wallet_get_capacity(
        #     self.account2["address"]["testnet"]
        # )
        # 5. Send payment using the created invoice
        self.fiber1.get_client().shutdown_channel(
            {
                "channel_id": N1N2_CHANNEL_ID,
                "close_script": {
                    "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
                    "hash_type": "type",
                    "args": self.account1["lock_arg"],
                },
                "fee_rate": "0x3FC",
                "force": True,
            }
        )
        time.sleep(20)

        # after_balance2 = self.Ckb_cli.wallet_get_capacity(
        #     self.account2["address"]["testnet"]
        # )
        # print("before_balance2:", before_balance2)
        # print("after_balance2:", after_balance2)
        # todo add check force close channel

    def test_force_udt(self):
        temporary_channel_id = self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(200 * 100000000),
                "public": True,
                # "tlc_fee_proportional_millionths": "0x4B0",
                "funding_udt_type_script": self.get_account_udt_script(
                    self.fiber1.account_private
                ),
            }
        )
        time.sleep(1)
        self.wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
        )
        time.sleep(1)

        invoice_balance = hex(50 * 100000000)

        invoice = self.fiber2.get_client().new_invoice(
            {
                "amount": invoice_balance,
                "currency": "Fibd",
                "description": "test invoice generated by node2",
                "expiry": "0xe10",
                "final_cltv": "0x28",
                "payment_preimage": self.generate_random_preimage(),
                "hash_algorithm": "sha256",
                "udt_type_script": self.get_account_udt_script(
                    self.fiber1.account_private
                ),
            }
        )
        before_channel = self.fiber1.get_client().list_channels({})
        time.sleep(1)
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
        channels = self.fiber1.get_client().list_channels(
            {"peer_id": self.fiber2.get_peer_id()}
        )
        N1N2_CHANNEL_ID = channels["channels"][0]["channel_id"]

        # 5. Send payment using the created invoice
        self.fiber1.get_client().shutdown_channel(
            {
                "channel_id": N1N2_CHANNEL_ID,
                "close_script": {
                    "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
                    "hash_type": "type",
                    "args": self.account1["lock_arg"],
                },
                "fee_rate": "0x3FC",
                "force": True,
            }
        )
        time.sleep(20)
        after_account = self.udtContract.list_cell(
            self.node.getClient(),
            self.get_account_script(self.fiber1.account_private)["args"],
            self.get_account_script(self.fiber2.account_private)["args"],
        )
        print("after_account:", after_account)
        # todo check
