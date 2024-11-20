import datetime
import time

import pytest

from framework.basic_fiber import FiberTest


class TestListChannels(FiberTest):
    """
    状态
    -  显示 pending 的channels
    -  显示待 accept 的channel
    -  显示 closed channels 信息
    -  显示 channel 的其他信息
    -  显示 accept dan没成功的channel
    -  显示 下线的channel? 如何判断channels 是否在线
    """

    # FiberTest.debug = True

    def test_peer_id(self):
        """
        only show peer id 's  channels

        Returns:
        """
        account3_private_key = self.generate_account(1000)
        fiber3 = self.start_new_fiber(account3_private_key)
        fiber3.connect_peer(self.fiber1)
        temporary_channel_id = self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(1000 * 100000000),
                "public": True,
                "funding_udt_type_script": self.get_account_udt_script(
                    self.fiber1.account_private
                ),
            }
        )
        self.wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
        )

        temporary_channel_id = self.fiber1.get_client().open_channel(
            {
                "peer_id": fiber3.get_peer_id(),
                "funding_amount": hex(1000 * 100000000),
                "public": True,
            }
        )
        self.wait_for_channel_state(
            self.fiber1.get_client(), fiber3.get_peer_id(), "CHANNEL_READY", 120
        )
        n12_channels = self.fiber1.get_client().list_channels(
            {"peer_id": self.fiber2.get_peer_id()}
        )

        n21_channels = self.fiber2.get_client().list_channels(
            {"peer_id": self.fiber1.get_peer_id()}
        )
        assert (
            n12_channels["channels"][0]["channel_id"]
            == n21_channels["channels"][0]["channel_id"]
        )

        n13_channels = self.fiber1.get_client().list_channels(
            {"peer_id": fiber3.get_peer_id()}
        )
        n31_channels = fiber3.get_client().list_channels(
            {"peer_id": self.fiber1.get_peer_id()}
        )
        assert (
            n13_channels["channels"][0]["channel_id"]
            == n31_channels["channels"][0]["channel_id"]
        )

    def test_empty(self):
        """
        show all channels
        Returns:
        """
        account3_private_key = self.generate_account(1000)
        fiber3 = self.start_new_fiber(account3_private_key)
        fiber3.connect_peer(self.fiber1)
        temporary_channel_id = self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(1000 * 100000000),
                "public": True,
                "funding_udt_type_script": self.get_account_udt_script(
                    self.fiber1.account_private
                ),
            }
        )
        self.wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
        )

        temporary_channel_id = self.fiber1.get_client().open_channel(
            {
                "peer_id": fiber3.get_peer_id(),
                "funding_amount": hex(1000 * 100000000),
                "public": True,
            }
        )
        self.wait_for_channel_state(
            self.fiber1.get_client(), fiber3.get_peer_id(), "CHANNEL_READY", 120
        )
        channels = self.fiber1.get_client().list_channels({})
        assert len(channels["channels"]) == 2

    def test_funding_udt_type_script(self):
        """
        funding_udt_type_script

        Returns:
        """
        account3_private_key = self.generate_account(1000)
        fiber3 = self.start_new_fiber(account3_private_key)
        fiber3.connect_peer(self.fiber1)
        temporary_channel_id = self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(1000 * 100000000),
                "public": True,
                "funding_udt_type_script": self.get_account_udt_script(
                    self.fiber1.account_private
                ),
            }
        )
        self.wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
        )
        channels = self.fiber1.get_client().list_channels({})
        assert channels["channels"][0][
            "funding_udt_type_script"
        ] == self.get_account_udt_script(self.fiber1.account_private)

    @pytest.mark.skip("pass")
    def test_funding_udt_type_script_none(self):
        """
        funding_udt_type_script: none  ==  ckb
        Returns:
        """

    def test_created_at(self):
        """

        Returns:

        """
        account3_private_key = self.generate_account(1000)
        fiber3 = self.start_new_fiber(account3_private_key)
        fiber3.connect_peer(self.fiber1)
        temporary_channel_id = self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(1000 * 100000000),
                "public": True,
                "funding_udt_type_script": self.get_account_udt_script(
                    self.fiber1.account_private
                ),
            }
        )
        self.wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
        )
        channels = self.fiber1.get_client().list_channels({})
        created_at_hex = int(channels["channels"][0]["created_at"], 16) / 1000

        assert int(created_at_hex / 1000) == int(
            int(datetime.datetime.now().timestamp()) / 1000
        )

    def test_is_public(self):
        """
        Returns:
        """
        temporary_channel_id = self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(1000 * 100000000),
                "public": True,
                "funding_udt_type_script": self.get_account_udt_script(
                    self.fiber1.account_private
                ),
            }
        )
        self.wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
        )
        channels = self.fiber1.get_client().list_channels({})
        assert channels["channels"][0]["is_public"] == True

    def test_channel_outpoint(self):
        """
        Returns:
        """
        temporary_channel_id = self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(1000 * 100000000),
                "public": True,
                "funding_udt_type_script": self.get_account_udt_script(
                    self.fiber1.account_private
                ),
            }
        )
        # self.wait_for_channel_state(
        #     self.fiber1.get_client(), self.fiber2.get_peer_id(), "NEGOTIATING_FUNDING", 120
        # )
        # channels = self.fiber1.get_client().list_channels({"peer_id": self.fiber2.get_peer_id()})
        # assert channels['channels'][0]['channel_outpoint'] is None
        self.wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
        )
        channels = self.fiber1.get_client().list_channels(
            {"peer_id": self.fiber2.get_peer_id()}
        )
        assert channels["channels"][0]["channel_outpoint"] is not None
        print("channel_outpoint:", channels["channels"][0]["channel_outpoint"])

    @pytest.mark.skip("close channels can't found")
    def test_close_channels(self):
        temporary_channel_id = self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(1000 * 100000000),
                "public": True,
                "funding_udt_type_script": self.get_account_udt_script(
                    self.fiber1.account_private
                ),
            }
        )

        self.wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
        )
        channels = self.fiber1.get_client().list_channels(
            {"peer_id": self.fiber2.get_peer_id()}
        )
        N1N2_CHANNEL_ID = channels["channels"][0]["channel_id"]
        self.fiber1.get_client().shutdown_channel(
            {
                "channel_id": N1N2_CHANNEL_ID,
                "close_script": self.get_account_script(self.Config.ACCOUNT_PRIVATE_1),
                "fee_rate": "0x3FC",
            }
        )
        # todo query shutdown_channel
        # self.wait_for_channel_state(self.fiber1.get_client(), self.fiber2.get_peer_id(), "Closed")
        # time.sleep(5)
        # self.fiber1.get_client().list_channels({})
