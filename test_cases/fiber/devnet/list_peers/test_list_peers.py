from framework.basic_fiber import FiberTest


class TestListPeers(FiberTest):

    def test_01(self):
        peer = self.fiber1.get_client().list_peers()
        assert (
            peer["peers"][0]["pubkey"]
            == self.fiber2.get_client().node_info()["node_id"]
        )
        assert (
            peer["peers"][0]["addresses"]
            == self.fiber2.get_client().node_info()["addresses"]
        )
        assert (
            peer["peers"][0]["peer_id"]
            == self.fiber2.get_client().node_info()["addresses"][0].split("/")[-1]
        )
