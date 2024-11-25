import time

from framework.basic_fiber import FiberTest


class TestGraphNodes(FiberTest):
    """

    1. add nodes

    2. remove nodes
        todo

    """

    def test_add_nodes(self):
        """
        add nodes
        """
        # add nodes
        graph_nodes = self.fiber1.get_client().graph_nodes()
        assert len(graph_nodes["nodes"]) == 2
        account3_private = self.generate_account(1000)
        fiber3 = self.start_new_fiber(account3_private)
        fiber3.connect_peer(self.fiber2)
        time.sleep(3)
        graph_nodes = self.fiber2.get_client().graph_nodes()
        assert len(graph_nodes["nodes"]) == 3
        graph_nodes = self.fiber1.get_client().graph_nodes()
        assert len(graph_nodes["nodes"]) == 3
