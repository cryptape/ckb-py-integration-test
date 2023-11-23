from framework.basic import CkbTest


class CKbLightClientLinkV110Node(CkbTest):

    def teardown_method(self, method):
        super().teardown_method(method)
        self.cluster.stop_all_nodes()
        self.cluster.clean_all_nodes()
        self.ckb_light_node.stop()
        self.ckb_light_node.clean()

    def test_110_main_link_ckb_light_successful(self):
        """
        Using the 110 mainnet configuration to connect to a light node, connection successful.

        1. Deploying 4 nodes with the mainnet configuration.
                Deployment successful.

        2. Mining 2,000 blocks.
            Mining successful.

        3. Starting the light node and connecting to 4 full nodes.
            Connection successful, light node started successfully.

        4. Synchronizing the script.
            Synchronization of height to 2,000 blocks successful.
        Returns:

        """
        nodes = [
            self.CkbNode.init_dev_by_port(self.CkbNodeConfigPath.V110_MAIN, "cluster/hardfork/node{i}".format(i=i),
                                          8124 + i,
                                          8225 + i)
            for
            i in range(1, 5)
        ]
        self.cluster = self.Cluster(nodes)
        self.cluster.prepare_all_nodes()
        self.cluster.start_all_nodes()
        self.cluster.connected_all_nodes()

        self.Miner.make_tip_height_number(self.cluster.ckb_nodes[0], 2000)
        self.Node.wait_cluster_height(self.cluster, 2000, 100)

        self.ckb_light_node = self.CkbLightClientNode.init_by_nodes(self.CkbLightClientConfigPath.CURRENT_TEST,
                                                                          self.cluster.ckb_nodes,
                                                                          "tx_pool_light/node1", 8001)
        self.ckb_light_node.prepare()
        self.ckb_light_node.start()
        account = self.Ckb_cli.util_key_info_by_private_key(self.Config.MINER_PRIVATE_1)
        self.ckb_light_node.getClient().set_scripts([{"script": {
            "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8", "hash_type": "type",
            "args": account['lock_arg']}, "script_type": "lock", "block_number": "0x0"}])
        self.Node.wait_light_sync_height(self.ckb_light_node, 2000, 200)

    def test_110_testnet_link_ckb_light_successful(self):
        """
        Using the 110 testnet configuration to connect to a light node, connection successful.

        1. Deploying 4 nodes with the mainnet configuration.
                Deployment successful.

        2. Mining 2,000 blocks.
            Mining successful.

        3. Starting the light node and connecting to 4 full nodes.
            Connection successful, light node started successfully.

        4. Synchronizing the script.
            Synchronization of height to 2,000 blocks successful.
        Returns:

        """
        nodes = [
            self.CkbNode.init_dev_by_port(self.CkbNodeConfigPath.V110_TEST, "cluster/hardfork/node{i}".format(i=i),
                                          8124 + i,
                                          8225 + i)
            for
            i in range(1, 5)
        ]
        self.cluster = self.Cluster(nodes)
        self.cluster.prepare_all_nodes()
        self.cluster.start_all_nodes()
        self.cluster.connected_all_nodes()

        self.Miner.make_tip_height_number(self.cluster.ckb_nodes[0], 2000)
        self.Node.wait_cluster_height(self.cluster, 2000, 100)

        self.ckb_light_node = self.CkbLightClientNode.init_by_nodes(self.CkbLightClientConfigPath.CURRENT_TEST,
                                                                          self.cluster.ckb_nodes,
                                                                          "tx_pool_light/node1", 8001)
        self.ckb_light_node.prepare()
        self.ckb_light_node.start()
        account = self.Ckb_cli.util_key_info_by_private_key(self.Config.MINER_PRIVATE_1)
        self.ckb_light_node.getClient().set_scripts([{"script": {
            "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8", "hash_type": "data2",
            "args": account['lock_arg']}, "script_type": "lock", "block_number": "0x0"}])
        self.Node.wait_light_sync_height(self.ckb_light_node, 2000, 200)

    def test_110_devnet_link_ckb_light_failed(self):
        """
        Using the 110 mainnet configuration to connect to a light node, connection successful.

        1. Deploying 4 nodes with the mainnet configuration.
                Deployment successful.

        2. Mining 100 blocks.
            Mining successful.

        3. Starting the light node and connecting to 4 full nodes.
            Connection failed, light node panic :
                thread 'main' panicked at 'load spec should be OK: Error { inner: ErrorInner { kind: Custom, line: Some(105), col: 0, at: Some(3266), message: "unknown field `rfc_0028`, expected `ckb2023`", key: ["params", "hardfork"] } }', src/subcmds.rs:36:10

        Returns:

        """
        nodes = [
            self.CkbNode.init_dev_by_port(self.CkbNodeConfigPath.V110, "cluster/hardfork/node{i}".format(i=i),
                                          8114 + i,
                                          8225 + i)
            for
            i in range(1, 5)
        ]
        self.cluster = self.Cluster(nodes)
        self.cluster.prepare_all_nodes()
        self.cluster.start_all_nodes()
        self.cluster.connected_all_nodes()

        self.Miner.make_tip_height_number(self.cluster.ckb_nodes[0], 100)
        self.Node.wait_cluster_height(self.cluster, 100, 100)

        self.ckb_light_node = self.CkbLightClientNode.init_by_nodes(self.CkbLightClientConfigPath.CURRENT_TEST,
                                                                          self.cluster.ckb_nodes,
                                                                          "tx_pool_light/node1", 8001)
        self.ckb_light_node.prepare()
        self.ckb_light_node.start()
        with open(f"{self.ckb_light_node.tmp_path}/node.log") as f:
            log = f.read()
            assert "panicked" in log
