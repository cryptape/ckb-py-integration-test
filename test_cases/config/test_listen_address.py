from framework.basic import CkbTest


class TestListenAddress(CkbTest):

    def test_listen_address(self):
        """
        fix: fix multi-listen with tcp bind #4889
        Returns:

        """
        self.node = self.CkbNode.init_dev_by_port(
            self.CkbNodeConfigPath.CURRENT_TEST, "node/node", 8118, 8119
        )
        self.node.prepare()
        self.node.prepare(
            other_ckb_config={
                "ckb_network_listen_addresses": [
                    "/ip4/0.0.0.0/tcp/8115",
                    "/ip4/0.0.0.0/tcp/8116",
                ],
                "ckb_network_reuse_tcp_with_ws": "true",
            }
        )
        self.node.start()
        local_node_info = self.node.getClient().local_node_info()
        assert len(local_node_info["addresses"]) == 4
        self.node.stop()
        self.node.clean()
