from framework.basic_fiber import FiberTest


class TestCommitmentDelayEpoch(FiberTest):

    def test_epoch(self):
        self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(1000 * 100000000),
                "public": True,
                "commitment_delay_epoch": hex(2),
            }
        )
        self.wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
        )
        self.fiber1.get_client().shutdown_channel(
            {
                "channel_id": self.fiber1.get_client().list_channels({})["channels"][0][
                    "channel_id"
                ],
                "close_script": {
                    "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
                    "hash_type": "type",
                    "args": self.account1["lock_arg"],
                },
                "fee_rate": "0x3FC",
                "force": True,
            }
        )
        tx_hash = self.wait_and_check_tx_pool_fee(1000, False)
        self.Miner.miner_until_tx_committed(self.node, tx_hash)
        self.node.getClient().generate_epochs(hex(2))
        tx_hash = self.wait_and_check_tx_pool_fee(1000, False, 1200)
        self.Miner.miner_until_tx_committed(self.node, tx_hash)
        message = self.get_tx_message(tx_hash)
        print(message)
        assert {
            "args": "0x470dcdc5e44064909650113a274b3b36aecb6dc7",
            "capacity": 6199999545,
        } in message["output_cells"]
        assert {
            "args": "0xc8328aabcd9b9e8e64fbc566c4385c3bdeb219d7",
            "capacity": 99999999545,
        } in message["output_cells"]
