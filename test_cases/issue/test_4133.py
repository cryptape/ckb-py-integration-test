import json

from framework.basic import CkbTest



class Test4133(CkbTest):

    def test_4133(self):
        """
            issue link:https://github.com/nervosnetwork/ckb/pull/4142
            No duplicate addr_manager will be stored.
            Note: When a node is closed, addr_manager will be updated, and last_connected_at_ms will be updated.
            1. Start nodes 1 and 2.
                Start successful.
            2. Nodes 1 and 2 connect.
                Connection successful.
            3. Close node 1, and read the addr_manager file.
                Closed successfully, addr_manager file is read.
            4. Restart node 1, connect to node 2, then close, and read the addr_manager file.
                There will only be 2 peers in addr_manager, and last_connected_at_ms will be updated.
        Returns:
        """
        node1 = self.CkbNode.init_dev_by_port(self.CkbNodeConfigPath.CURRENT_TEST, "issue/node1", 8914,
                                              8927)
        self.node1 = node1
        node1.prepare(
            other_ckb_config={'ckb_logger_filter': 'debug'}
        )
        node1.start()
        self.Miner.make_tip_height_number(node1, 100)
        node2 = self.CkbNode.init_dev_by_port(self.CkbNodeConfigPath.CURRENT_TEST, "issue/node2", 8915,
                                              8928)
        self.node2 = node2
        node2.prepare()
        node2.start()
        node1.connected(node2)
        self.Node.wait_node_height(node2, 100, 150)

        node1.stop()
        with open(f"{node1.ckb_dir}/data/network/peer_store/addr_manager.db", 'r') as f:
            addr_managers = f.read()
        addr_manager1 = json.loads(addr_managers)
        node1.start()
        node1.connected(node2)
        self.Miner.make_tip_height_number(node1, 200)
        self.Node.wait_node_height(node2, 200, 150)
        node1.stop()
        with open(f"{node1.ckb_dir}/data/network/peer_store/addr_manager.db", 'r') as f:
            addr_managers = f.read()
        addr_manager2 = json.loads(addr_managers)
        assert len(addr_manager2) == len(addr_manager1)
        assert len(addr_manager2) == 2

        current_last_connected_at_ms = addr_manager2[1]['last_connected_at_ms'] if addr_manager2[0][
                                                                                       'last_connected_at_ms'] == 0 else \
            addr_manager2[0][
                'last_connected_at_ms']
        pre_last_connected_at_ms = addr_manager1[1]['last_connected_at_ms'] if addr_manager1[0][
                                                                                   'last_connected_at_ms'] == 0 else \
            addr_manager1[0][
                'last_connected_at_ms']
        assert current_last_connected_at_ms > pre_last_connected_at_ms

    def teardown_method(self, method):
        super().teardown_method(method)
        print("\nTearing down method", method.__name__)
        self.node1.stop()
        self.node1.clean()
        self.node2.stop()
        self.node2.clean()
