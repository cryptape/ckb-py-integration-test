import time


from framework.basic import CkbTest
from framework.util import get_project_root


class TestCkbLightClientAfterHardFork(CkbTest):

    @classmethod
    def setup_class(cls):
        nodes = [
            cls.CkbNode.init_dev_by_port(cls.CkbNodeConfigPath.CURRENT_TEST, "cluster/hardfork/node{i}".format(i=i),
                                         8124 + i,
                                         8225 + i)
            for
            i in range(1, 5)
        ]
        cls.cluster = cls.Cluster(nodes)
        cls.cluster.prepare_all_nodes()
        cls.cluster.start_all_nodes()
        cls.cluster.connected_all_nodes()
        contracts = cls.Contract_util.deploy_contracts(cls.Config.ACCOUNT_PRIVATE_1, cls.cluster.ckb_nodes[0])
        cls.spawn_contract = contracts["SpawnContract"]

        cls.Miner.make_tip_height_number(cls.cluster.ckb_nodes[0], 20)
        cls.Node.wait_cluster_height(cls.cluster, 20, 100)

        cls.ckb_light_node_current = cls.CkbLightClientNode.init_by_nodes(cls.CkbLightClientConfigPath.CURRENT_TEST,
                                                                          cls.cluster.ckb_nodes,
                                                                          "tx_pool_light/node1", 8001)

        cls.ckb_light_node_current.prepare()
        cls.ckb_light_node_current.start()
        account = cls.Ckb_cli.util_key_info_by_private_key(cls.Config.MINER_PRIVATE_1)
        cls.ckb_light_node_current.getClient().set_scripts([{"script": {
            "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8", "hash_type": "type",
            "args": account['lock_arg']}, "script_type": "lock", "block_number": "0x0"}])
        cls.Node.wait_light_sync_height(cls.ckb_light_node_current, 20, 200)

    @classmethod
    def teardown_class(cls):
        print("\nTeardown TestClass1")
        cls.cluster.stop_all_nodes()
        cls.cluster.clean_all_nodes()
        cls.ckb_light_node_current.stop()
        cls.ckb_light_node_current.clean()

    def test_01_ckb_light_client_deploy_and_invoke_contract(self):
        self.cluster.ckb_nodes[0].start_miner()
        self.deploy_and_invoke(self.Config.MINER_PRIVATE_1,
                               f"{get_project_root()}/source/contract/test_cases/always_success",
                               self.cluster.ckb_nodes[0])
        self.cluster.ckb_nodes[0].stop_miner()

    def deploy_and_invoke(self, account, path, node, try_count=5):
        if try_count < 0:
            raise Exception("try out of times")
        try:
            deploy_hash = self.Contract.deploy_ckb_contract(account,
                                                            path,
                                                            enable_type_id=True,
                                                            api_url=node.getClient().url)
            self.Miner.miner_until_tx_committed(node, deploy_hash)
            self.Node.wait_light_sync_height(self.ckb_light_node_current, node.getClient().get_tip_block_number(), 200)
            self.Node.wait_fetch_transaction(self.ckb_light_node_current, deploy_hash, "fetched")
            tx_msg = self.Contract.build_invoke_ckb_contract(account_private=account,
                                                             contract_out_point_tx_hash=deploy_hash,
                                                             contract_out_point_tx_index=0,
                                                             type_script_arg="0x02", data="0x1234",
                                                             hash_type="type",
                                                             api_url=node.getClient().url)
            self.Node.wait_light_sync_height(self.ckb_light_node_current, node.getClient().get_tip_block_number(), 200)
            light_tx_hash = self.ckb_light_node_current.getClient().send_transaction(tx_msg)
            for i in range(100):
                light_ret = node.getClient().get_transaction(light_tx_hash)
                time.sleep(1)
                print("light ret status:", light_ret['tx_status']['status'])
                if light_ret['tx_status']['status'] != 'pending':
                    continue
                if light_ret['tx_status']['status'] == 'pending':
                    print("status is pending i:", i)
                    break
                if i == 99:
                    raise Exception("status is failed ")
            self.Miner.miner_until_tx_committed(node, light_tx_hash, with_unknown=True)
            return light_tx_hash
        except Exception as e:
            print(e)
            if "Resolve failed Dead" in str(e):
                try_count -= 1
                for i in range(2):
                    self.Miner.miner_with_version(node, "0x0")
                time.sleep(3)
                return self.deploy_and_invoke(account, path, node, try_count)
            if "PoolRejectedRBF" in str(e):
                try_count -= 1
                for i in range(2):
                    self.Miner.miner_with_version(node, "0x0")
                time.sleep(3)
                return self.deploy_and_invoke(account, path, node, try_count)
            raise e
