from framework.basic import CkbTest


class CyclingAttack(CkbTest):

    @classmethod
    def setup_class(cls):
        cls.node1 = cls.CkbNode.init_dev_by_port(
            cls.CkbNodeConfigPath.v117, "node/node1", 8119, 8125
        )

        cls.node1.prepare()
        cls.node1.start()
        cls.Miner.make_tip_height_number(cls.node1, 100)

    @classmethod
    def teardown_class(cls):
        cls.node1.stop()
        cls.node1.clean()

    def test_01(self):
        """
        1. B0 ---> B1
        2. A0 ---> A1 ---> A2
        3. A1 , B0 --> B2(big fee )
        3. B1 status ：rejected, A2 status: rejected
        4. A0 -> A3 (big fee)
        5. B2 statue: rejected
        6. wait a3 committed
        7. b1 status: committed
        Returns:
        """
        account = self.Ckb_cli.util_key_info_by_private_key(
            self.Config.ACCOUNT_PRIVATE_1
        )
        account_private = self.Config.ACCOUNT_PRIVATE_1
        tx1_hash = self.Ckb_cli.wallet_transfer_by_private_key(
            account_private,
            account["address"]["testnet"],
            1000000,
            self.node1.getClient().url,
            "1500000",
        )

        tx_father_hash = self.Tx.send_transfer_self_tx_with_input(
            [tx1_hash],
            ["0x0"],
            account_private,
            output_count=2,
            fee=1090000,
            api_url=self.node1.getClient().url,
        )

        self.Miner.miner_until_tx_committed(self.node1, tx_father_hash)
        # 1. B0 ---> B1
        tx_b0 = tx_father_hash
        tx_b0_index = "0x0"
        tx_b1 = self.Tx.send_transfer_self_tx_with_input(
            [tx_b0],
            [tx_b0_index],
            account_private,
            output_count=1,
            fee=1000,
            api_url=self.node1.getClient().url,
        )

        # 2. A0 ---> A1 ---> A2
        tx_a0 = tx_father_hash
        tx_a0_index = "0x1"
        tx_a1 = self.Tx.send_transfer_self_tx_with_input(
            [tx_a0],
            [tx_a0_index],
            account_private,
            output_count=1,
            fee=1000,
            api_url=self.node1.getClient().url,
        )

        tx_a2 = self.Tx.send_transfer_self_tx_with_input(
            [tx_a1],
            ["0x0"],
            account_private,
            output_count=1,
            fee=1000,
            api_url=self.node1.getClient().url,
        )

        # 3. A1 , B0 --> B2
        tx_b2 = self.Tx.send_transfer_self_tx_with_input(
            [tx_a0, tx_b0],
            [tx_a0_index, tx_b0_index],
            account_private,
            output_count=1,
            fee=100000,
            api_url=self.node1.getClient().url,
        )
        # 3. B1 status ：rejected, A2 status: rejected
        tx_b1_response = self.node1.getClient().get_transaction(tx_b1)
        tx_a2_response = self.node1.getClient().get_transaction(tx_a2)
        print("tx_b1_response:", tx_b1_response)
        print("tx_a2_response:", tx_a2_response)

        # 4. A0 -> A3
        tx_a3 = self.Tx.send_transfer_self_tx_with_input(
            [tx_a0],
            [tx_a0_index],
            account_private,
            output_count=1,
            fee=10000000,
            api_url=self.node1.getClient().url,
        )
        # 5. B2 statue: rejected
        tx_b2_response = self.node1.getClient().get_transaction(tx_b2)
        print("tx_b2_response:", tx_b2_response)

        # 6. wait a3 committed
        self.Miner.miner_until_tx_committed(self.node1, tx_a3)

        # 7. b1 status: committed
        self.Miner.miner_until_tx_committed(self.node1, tx_b1)
