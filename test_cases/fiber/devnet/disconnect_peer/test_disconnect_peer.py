import time

from framework.basic_fiber import FiberTest


class TestDisconnectPeer(FiberTest):
    def test_disconnect_peer(self):
        before_node_info = self.fiber1.get_client().node_info()
        assert before_node_info["peers_count"] == "0x1"

        self.fiber1.get_client().disconnect_peer(
            {"peer_id": self.fiber2.get_client().node_info()["peer_id"]}
        )
        time.sleep(1)
        after_node_info = self.fiber1.get_client().node_info()
        assert after_node_info["peers_count"] == "0x0"

        # not exist peer_id
        self.fiber1.get_client().disconnect_peer(
            {"peer_id": "QmNoDjLNbJujKpBorKHWPHPKoLrzND1fYtmmEVxkq35Hgp"}
        )
