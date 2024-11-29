import time

from framework.basic_fiber import FiberTest


class TestConnectPeer(FiberTest):

    def test_connect_peer(self):
        # exist node
        self.fiber1.connect_peer(self.fiber2)
        # not exist node
        self.fiber1.get_client().connect_peer(
            {
                "address": "/ip4/127.0.0.1/tcp/8231/p2p/QmNoDjLNbJujKpBorKHWPHPKoLrzND1fYtmmEVxkq35Hgp"
            }
        )
        time.sleep(2)
        node_info = self.fiber1.get_client().node_info()
        assert node_info["peers_count"] == "0x1"
