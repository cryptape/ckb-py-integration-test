import pytest

from framework.basic import CkbTest


class TestLightSync(CkbTest):
    node: CkbTest.CkbNode
    cluster: CkbTest.Cluster
    ckb_light_node: CkbTest.CkbLightClientNode

    @classmethod
    def setup_class(cls):
        node1 = cls.CkbNode.init_dev_by_port(cls.CkbNodeConfigPath.V113, "tx_pool_main/node1", 8115,
                                             8227)
        node2 = cls.CkbNode.init_dev_by_port(cls.CkbNodeConfigPath.V113, "tx_pool_main/node2", 8116,
                                             8228)

        cls.node = node1
        cls.node2 = node2
        cls.cluster = cls.Cluster([node1, node2])
        node1.prepare(other_ckb_spec_config={"ckb_params_genesis_epoch_length": "1", "ckb_name": "ckb_dev",
                                             "ckb_params_genesis_compact_target": "0x2020000"})
        node2.prepare(other_ckb_spec_config={"ckb_params_genesis_epoch_length": "1", "ckb_name": "ckb_dev",
                                             "ckb_params_genesis_compact_target": "0x2020000"})

        cls.cluster.start_all_nodes()
        cls.cluster.connected_all_nodes()
        cls.Miner.make_tip_height_number(cls.node, 13000)
        cls.Node.wait_cluster_height(cls.cluster, 5, 13000)
        node1.start_miner()

    @classmethod
    def teardown_class(cls):
        print("\nTeardown TestClass1")
        cls.cluster.stop_all_nodes()
        cls.cluster.clean_all_nodes()

    def test_sync(self):
        for i in range(10):
            print("current idx", i)
            self.ckb_light_node = self.CkbLightClientNode.init_by_nodes(self.CkbLightClientConfigPath.CURRENT_TEST,
                                                                        [self.node, self.node2],
                                                                        "tx_pool_light/node1", 8001)
            self.ckb_light_node.prepare()
            self.ckb_light_node.start()

            old_sync_account = [
                self.Config.ACCOUNT_PRIVATE_1,
                self.Config.ACCOUNT_PRIVATE_2
            ]
            new_sync_account = [
                self.Config.MINER_PRIVATE_1
            ]
            old_sync_block_number = 6000
            new_sync_block_number = 3000
            add_sync_new_account_block_number = 8000
            new_sync_until_number = 12000

            print("sync old account")
            setScripts = []
            for account_private in old_sync_account:
                acc = self.Ckb_cli.util_key_info_by_private_key(account_private)
                setScripts.append({"script": {
                    "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
                    "hash_type": "type",
                    "args": acc['lock_arg']}, "script_type": "lock", "block_number": hex(old_sync_block_number)})
            self.ckb_light_node.getClient().set_scripts(setScripts)

            print(f"until sync:{add_sync_new_account_block_number}")
            self.Node.wait_light_sync_height(self.ckb_light_node, add_sync_new_account_block_number, 1000000)
            print("sync new account ")
            scripts = self.ckb_light_node.getClient().get_scripts()
            newSetScripts = []
            for i in scripts:
                newSetScripts.append(i)
            for account_private in new_sync_account:
                acc = self.Ckb_cli.util_key_info_by_private_key(account_private)
                newSetScripts.append({"script": {
                    "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
                    "hash_type": "type",
                    "args": acc['lock_arg']}, "script_type": "lock", "block_number": hex(new_sync_block_number)})
            self.ckb_light_node.getClient().set_scripts(newSetScripts)
            print("until sync ")
            self.Node.wait_light_sync_height(self.ckb_light_node, new_sync_until_number, 100000)
            print("compare new account data")
            for acc in new_sync_account:
                print("------------~~~----------------------")
                acc = self.Ckb_cli.util_key_info_by_private_key(acc)
                light_cells = self.ckb_light_node.getClient().get_cells({
                    "script": {
                        "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
                        "hash_type": "type",
                        "args": acc['lock_arg']
                    },
                    "script_type": "lock",
                    "filter": {
                        "block_range": [hex(new_sync_block_number), hex(new_sync_until_number)]
                    }}, "asc", "0xffffff", None)
                full_cells = self.node.getClient().get_cells({
                    "script": {
                        "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
                        "hash_type": "type",
                        "args": acc['lock_arg']
                    },
                    "script_type": "lock",
                    "filter": {
                        "block_range": [hex(new_sync_block_number + 1), hex(new_sync_until_number)]
                    }}, "asc", "0xffffff", None)
                assert len(light_cells['objects']) == len(full_cells['objects'])
                print(len(light_cells['objects']))
                print(len(full_cells['objects']))
            self.ckb_light_node.stop()
            self.ckb_light_node.clean()
