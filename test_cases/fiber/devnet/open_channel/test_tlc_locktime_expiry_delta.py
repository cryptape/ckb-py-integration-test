import time

import pytest

from framework.basic_fiber import FiberTest


class TestTlcLocktimeExpiryDelta(FiberTest):

    @pytest.mark.skip("todo")
    def test_tlc_locktime_expiry_delta_none(self):
        """
        tlc_locktime_expiry_delta = none
        Returns:
        """
        # self.test_linked_peer()

    def test_tlc_locktime_expiry_delta_is_zero(self):
        """
        tlc_locktime_expiry_delta = 0
        Returns:
        """

        temporary_channel_id = self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(200 * 100000000),
                "public": True,
                "tlc_locktime_expiry_delta": "0x0",
                # "tlc_fee_proportional_millionths": "0x4B0",
            }
        )
        self.wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
        )
        time.sleep(1)
        # transfer
        self.fiber1.get_client().graph_channels()
        self.fiber1.get_client().graph_nodes()
        payment_preimage = self.generate_random_preimage()
        invoice_balance = 100 * 100000000
        invoice = self.fiber2.get_client().new_invoice(
            {
                "amount": hex(invoice_balance),
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
        assert (
            int(before_channel["channels"][0]["local_balance"], 16)
            - int(after_channel["channels"][0]["local_balance"], 16)
            == invoice_balance
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
        assert after_balance2 - before_balance2 == 162

    @pytest.mark.skip("todo")
    def test_tlc_locktime_expiry_delta_is_1(self):
        """
        tlc_locktime_expiry_delta = 1
        Returns:
        todo:
            qa: open_channel 的 tlc_locktime_expiry_delta 作用是什么呢？ 有点没理解 @by  我要怎么才能测到这个参数
             A 给 B 发送一个 tlc，如果 B 知道原相，那 B 可以取走 tlc 里面的资金，否则过了时间 tlc_locktime_expiry_delta 之后，A 可以取回 tlc 里面的资金。
            那a 可以怎么取回tlc的资金
            要在 watchtower 里面做，我们现在似乎没有这个功能
        """

    @pytest.mark.skip("todo")
    def test_tlc_locktime_expiry_delta_not_eq_default(self):
        """
        tlc_locktime_expiry_delta != default

        Returns:

        """