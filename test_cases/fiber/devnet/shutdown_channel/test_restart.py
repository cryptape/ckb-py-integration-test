import time

import pytest

from framework.basic_fiber import FiberTest


@pytest.mark.skip("todo")
class TestRestart(FiberTest):
    # FiberTest.debug = True
    # https://github.com/nervosnetwork/fiber/issues/246
    # 1. open_channel
    # 2. remove open_channel tx
    # 3. open_channel again
    # 4. open_channel again
    # 5. 等到5分钟 就复现
    def test_ckb_node_restart(self):
        self.node.restart()

    def test_01(self):
        """
        shutdown 过程重启
        - 发起方重启
        - 接受方重启
        Returns:

        """
        self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(1000 * 100000000),
                "public": True,
            }
        )
        open_channel_tx_hash = self.wait_and_check_tx_pool_fee(1000, False)
        # self.node.getClient().clear_tx_pool()
        self.wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY"
        )
        # shutdown channel
        N1N2_CHANNEL_ID = self.fiber1.get_client().list_channels({})["channels"][0][
            "channel_id"
        ]
        print(N1N2_CHANNEL_ID)
        # cell = self.node.getClient().get_live_cell("0x0", open_channel_tx_hash)
        # assert cell['status'] == "live"
        #
        # self.fiber1.get_client().shutdown_channel({
        #     "channel_id": N1N2_CHANNEL_ID,
        #     "close_script": {
        #         "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
        #         "hash_type": "type",
        #         "args": self.account1["lock_arg"],
        #     },
        #     "fee_rate": "0x3FC",
        # })
        # self.node.stop()
        # time.sleep(10)
        # self.node.start()
        # self.fiber2.stop()
        # time.sleep(10)
        # result = self.node.getClient().get_live_cell("0x0", open_channel_tx_hash)
        # assert result['status'] == "live"
        # # self.wait_for_channel_state(self.fiber1.get_client(), self.fiber2.get_peer_id(), "SHUTTING_DOWN")
        # self.fiber1.stop()
        # time.sleep(10)
        # self.fiber1.start()
        # time.sleep(10)
        #
        # self.fiber2.start()
        # time.sleep(10)
        #
        # self.fiber1.get_client().list_channels({})
        # self.fiber2.get_client().list_channels({})
        # result = self.node.getClient().get_live_cell("0x0", open_channel_tx_hash)
        # assert result['status'] == "unknown"
        #

    def test_node2_open(self):
        self.fiber2.get_client().open_channel(
            {
                "peer_id": self.fiber1.get_peer_id(),
                "funding_amount": hex(1000 * 100000000),
                "public": True,
            }
        )

    def test_000(self):
        # self.fiber1.get_client().list_channels({})

        self.fiber2.get_client().node_info()
        # self.fiber2.stop()
        # self.node.getClient().get_live_cell("0x0", "0x964bedfcc81c9060a60d2495cb818b077caf83de0d5c35dfc1913cb4bcc05dec")
