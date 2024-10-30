import time

import pytest

from framework.basic_fiber import FiberTest


class TestCkbCell(FiberTest):
    # FiberTest.debug = True
    def test_account_cell_data_not_empty(self):
        """
        if account cell.data != empty
        Returns:
        """

    def test_account_cell_gt_funding_amount_10ckb(self):
        """
        cell - funding_amount = 10 ckb
        Returns:
            open channel FAILED
        """
        capacity = self.Ckb_cli.wallet_get_capacity(self.account2["address"]["testnet"])
        temporary_channel_id = self.fiber2.get_client().open_channel(
            {
                "peer_id": self.fiber1.get_peer_id(),
                "funding_amount": hex((int(capacity) - 10) * 100000000),
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

    def test_account_mutil_cell_gt_funding_amount(self):
        """
        https://github.com/nervosnetwork/fiber/issues/284
         N cell balance > funding_amount
        Returns:
        """
        account3_private_key = (
            "0x100c06bfd800d27397002dca6fb0993d5ba6399b4238b2f29ee9deb97593d2b1"
        )
        account3 = self.Ckb_cli.util_key_info_by_private_key(account3_private_key)
        tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(
            self.Config.ACCOUNT_PRIVATE_1,
            account3["address"]["testnet"],
            1000,
            self.node.rpcUrl,
        )
        self.Miner.miner_until_tx_committed(self.node, tx_hash)
        tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(
            self.Config.ACCOUNT_PRIVATE_1,
            account3["address"]["testnet"],
            1000,
            self.node.rpcUrl,
        )
        self.Miner.miner_until_tx_committed(self.node, tx_hash)

        # start fiber3
        new_fiber = self.start_new_fiber(
            account3_private_key,
            {
                "ckb_rpc_url": self.node.rpcUrl,
            },
        )
        new_fiber.connect_peer(self.fiber2)
        time.sleep(1)
        new_fiber.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(990 * 100000000),
                "public": True,
                # "tlc_fee_proportional_millionths": "0x4B0",
            }
        )
        self.wait_for_channel_state(
            new_fiber.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
        )
        channels = new_fiber.get_client().graph_channels()
        assert len(channels["channels"]) == 1
        assert channels["channels"][0]["capacity"] == hex(1052 * 100000000)

    def test_account_mutil_cell_gt_funding_amount_2(self):
        """
         N cell balance > funding_amount
        Returns:
        """
        account3_private_key = (
            "0x100c06bfd800d27397002dca6fb0993d5ba6399b4238b2f29ee9deb97593d2b1"
        )
        account3 = self.Ckb_cli.util_key_info_by_private_key(account3_private_key)
        tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(
            self.Config.ACCOUNT_PRIVATE_1,
            account3["address"]["testnet"],
            1000,
            self.node.rpcUrl,
        )
        self.Miner.miner_until_tx_committed(self.node, tx_hash)
        tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(
            self.Config.ACCOUNT_PRIVATE_1,
            account3["address"]["testnet"],
            1000,
            self.node.rpcUrl,
        )
        self.Miner.miner_until_tx_committed(self.node, tx_hash)

        # start fiber3
        new_fiber = self.start_new_fiber(account3_private_key)
        new_fiber.connect_peer(self.fiber2)
        time.sleep(1)
        new_fiber.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(990 * 100000000),
                "public": True,
                # "tlc_fee_proportional_millionths": "0x4B0",
            }
        )
        self.wait_for_channel_state(
            new_fiber.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
        )
        channels = new_fiber.get_client().graph_channels()
        assert len(channels["channels"]) == 1
        assert channels["channels"][0]["capacity"] == hex(1052 * 100000000)

    @pytest.mark.skip
    def test_open_chanel_same_time(self):
        """
        同时打开多个channel
        todo: add check : 创建channel 失败 需要终态
         Returns:
        """
        open_count = 5
        for i in range(open_count):
            account_private_key = self.generate_account(1000)
            fiber = self.start_new_fiber(account_private_key)
            fiber.connect_peer(self.fiber2)
        time.sleep(1)
        for i in range(open_count):
            self.new_fibers[i].get_client().open_channel(
                {
                    "peer_id": self.fiber2.get_peer_id(),
                    "funding_amount": hex(200 * 100000000),
                    "public": True,
                }
            )
            self.wait_for_channel_state(
                self.new_fibers[i].get_client(),
                self.fiber2.get_peer_id(),
                "CHANNEL_READY",
                120,
            )
        for i in range(open_count):
            self.wait_for_channel_state(
                self.new_fibers[i].get_client(),
                self.fiber2.get_peer_id(),
                "CHANNEL_READY",
                120,
            )
        send_payment_count = 10
        invoice_list = []
        for j in range(send_payment_count):
            print("current j:", j)
            invoice_list = []

            for i in range(open_count):
                payment_preimage = self.generate_random_preimage()
                invoice_balance = 1
                invoice = self.fiber2.get_client().new_invoice(
                    {
                        "amount": hex(invoice_balance),
                        "currency": "Fibb",
                        "description": "test invoice generated by node2",
                        "expiry": "0xe10",
                        "final_cltv": "0x28",
                        "payment_preimage": payment_preimage,
                        "hash_algorithm": "sha256",
                    }
                )
                invoice_list.append(invoice)
            for i in range(open_count):
                self.new_fibers[i].get_client().send_payment(
                    {
                        "invoice": invoice_list[i]["invoice_address"],
                    }
                )
            for i in range(open_count):
                self.wait_for_channel_state(
                    self.new_fibers[i].get_client(),
                    self.fiber2.get_peer_id(),
                    "CHANNEL_READY",
                    120,
                )
