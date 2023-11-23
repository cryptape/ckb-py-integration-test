import os
import time


from parameterized import parameterized

from framework.basic import CkbTest
from framework.util import get_project_root


def get_all_files(directory):
    file_list = []
    for root, directories, files in os.walk(directory):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            file_list.append(file_path)
    return file_list


# def get_successful_files():
#     files = get_all_files(f"{get_project_root()}/source/contract/test_cases")
#     files_list = ["spawn_exceeded_max_content_length",
#                   "loop_contract",
#                   "spawn_exec_memory_limit_le_7",
#                   "spawn_argc_not_eq",
#                   "spawn_argc_is_u64_max",
#                   "spawn_out_of_memory",
#                   "spawn_fib",
#                   "spawn_times"
#                   ]
#     []
#     return [s for s in files if not any(s.endswith(suffix) for suffix in files_list)]

def get_successful_files():
    return [
        f"{get_project_root()}/source/contract/test_cases/ckb_get_memory_limit",
        f"{get_project_root()}/source/contract/test_cases/atomic_i32",
        f"{get_project_root()}/source/contract/test_cases/spawn_current_cycles",
        # f"{get_project_root()}/source/contract/test_cases/load_block_extension", //TODO wait https://github.com/nervosnetwork/ckb-light-client/pull/156/files
    ]


class TestCkbLightClientAfterHardFork(CkbTest):
    success_files = get_successful_files()

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

        cls.Miner.make_tip_height_number(cls.cluster.ckb_nodes[0], 2000)
        cls.Node.wait_cluster_height(cls.cluster, 2000, 100)

        cls.ckb_light_node_0_2_5 = cls.CkbLightClientNode.init_by_nodes(cls.CkbLightClientConfigPath.CURRENT_TEST,
                                                                        cls.cluster.ckb_nodes,
                                                                        "tx_pool_light/node1", 8001)

        cls.ckb_light_node_0_2_5.prepare()
        cls.ckb_light_node_0_2_5.start()
        account = cls.Ckb_cli.util_key_info_by_private_key(cls.Config.MINER_PRIVATE_1)
        cls.ckb_light_node_0_2_5.getClient().set_scripts([{"script": {
            "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8", "hash_type": "type",
            "args": account['lock_arg']}, "script_type": "lock", "block_number": "0x0"}])
        cls.Node.wait_light_sync_height(cls.ckb_light_node_0_2_5, 2000, 200)


    @classmethod
    def teardown_class(cls):
        print("\nTeardown TestClass1")
        cls.cluster.stop_all_nodes()
        cls.cluster.clean_all_nodes()
        cls.ckb_light_node_0_2_5.stop()
        cls.ckb_light_node_0_2_5.clean()

    def test_01_ckb_light_client_0_2_4_link_node(self):
        pass

    def test_02_ckb_light_client_0_2_5_link_node(self):
        """
        1. setScript miner account
            set successful
        2. wait miner script sync
            sync successful
        Returns:

        """
        account = self.Ckb_cli.util_key_info_by_private_key(self.Config.MINER_PRIVATE_1)
        self.ckb_light_node_0_2_5.getClient().set_scripts([{"script": {
            "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8", "hash_type": "type",
            "args": account['lock_arg']}, "script_type": "lock", "block_number": "0x0"}])
        self.Node.wait_light_sync_height(self.ckb_light_node_0_2_5, 2000, 200)

    def test_03_ckb_light_client_0_2_5_set_script_data2(self):
        """
        1. set data2 account
            sync successful
        Returns:

        """
        account = self.Ckb_cli.util_key_info_by_private_key(self.Config.MINER_PRIVATE_1)
        self.ckb_light_node_0_2_5.getClient().set_scripts([{"script": {
            "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8", "hash_type": "data2",
            "args": account['lock_arg']}, "script_type": "lock", "block_number": "0x0"}])
        self.Node.wait_light_sync_height(self.ckb_light_node_0_2_5, 2000, 200)

    def test_04_ckb_light_client_0_2_5_transfer_data2_tx(self):
        """
        1. send data2 tx on the ckb light client
                send successful ,return tx_hash
        Returns:

        """
        self.cluster.ckb_nodes[0].start_miner()
        account = self.Ckb_cli.util_key_info_by_private_key(self.Config.MINER_PRIVATE_1)
        self.ckb_light_node_0_2_5.getClient().set_scripts([{"script": {
            "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8", "hash_type": "type",
            "args": account['lock_arg']}, "script_type": "lock", "block_number": "0x0"}])
        self.Node.wait_light_sync_height(self.ckb_light_node_0_2_5, 2000, 200)
        self.cluster.ckb_nodes[0].stop_miner()

        tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(self.Config.MINER_PRIVATE_1,
                                                              "ckt1qp5usrt2syzfjj7acyetk45vj57kp7hq4jfg4ky8e9k7ss6v52neqpqh7xtq0",
                                                              140,
                                                              self.cluster.ckb_nodes[0].client.url)
        tx = self.cluster.ckb_nodes[0].getClient().get_transaction(tx_hash)
        transaction = tx['transaction']
        tx_hash = transaction['hash']
        del transaction['hash']
        light_tx_hash = self.ckb_light_node_0_2_5.getClient().send_transaction(transaction)

        assert tx_hash == light_tx_hash

    def test_05_ckb_light_client_0_2_5_spawn_contract_use_data2(self):
        """
           1. send spawn tx ( hash type : data2), on the ckb light client
                   send successful ,return tx_hash
           Returns:
        """
        # send rfc50 tx
        self.cluster.ckb_nodes[0].start_miner()
        account = self.Ckb_cli.util_key_info_by_private_key(self.Config.MINER_PRIVATE_1)
        self.ckb_light_node_0_2_5.getClient().set_scripts([{"script": {
            "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8", "hash_type": "type",
            "args": account['lock_arg']}, "script_type": "lock", "block_number": "0x0"}])
        self.Node.wait_light_sync_height(self.ckb_light_node_0_2_5, 2000, 200)
        self.cluster.ckb_nodes[0].stop_miner()

        code_tx_hash, code_tx_index = self.spawn_contract.get_deploy_hash_and_index()
        invoke_arg, invoke_data = self.spawn_contract.get_arg_and_data("demo")
        tx_hash = self.Contract.invoke_ckb_contract(self.Config.MINER_PRIVATE_1, code_tx_hash, code_tx_index,
                                                    invoke_arg, "data2", invoke_data,
                                                    api_url=self.cluster.ckb_nodes[0].getClient().url)

        self.ckb_light_node_0_2_5.getClient().fetch_transaction(code_tx_hash)
        # TODO wait fetch tx succ
        time.sleep(5)
        self.ckb_light_node_0_2_5.getClient().fetch_transaction(code_tx_hash)
        tx = self.cluster.ckb_nodes[0].getClient().get_transaction(tx_hash)
        transaction = tx['transaction']
        tx_hash = transaction['hash']
        del transaction['hash']
        light_tx_hash = self.ckb_light_node_0_2_5.getClient().send_transaction(transaction)

        assert tx_hash == light_tx_hash

    def test_05_ckb_light_client_0_2_5_spawn_contract_use_type(self):
        """
           1. send spawn tx ( hash type : type), on the ckb light client
                   send successful ,return tx_hash
           Returns:
        """
        # send rfc50 tx
        self.cluster.ckb_nodes[0].start_miner()
        account = self.Ckb_cli.util_key_info_by_private_key(self.Config.MINER_PRIVATE_1)
        self.ckb_light_node_0_2_5.getClient().set_scripts([{"script": {
            "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8", "hash_type": "type",
            "args": account['lock_arg']}, "script_type": "lock", "block_number": "0x0"}])
        self.Node.wait_light_sync_height(self.ckb_light_node_0_2_5, 2000, 200)
        self.cluster.ckb_nodes[0].stop_miner()

        code_tx_hash, code_tx_index = self.spawn_contract.get_deploy_hash_and_index()
        invoke_arg, invoke_data = self.spawn_contract.get_arg_and_data("demo")
        tx_hash = self.Contract.invoke_ckb_contract(self.Config.MINER_PRIVATE_1, code_tx_hash, code_tx_index,
                                                    invoke_arg, "type", invoke_data,
                                                    api_url=self.cluster.ckb_nodes[0].getClient().url)

        self.ckb_light_node_0_2_5.getClient().fetch_transaction(code_tx_hash)
        time.sleep(5)
        self.ckb_light_node_0_2_5.getClient().fetch_transaction(code_tx_hash)
        tx = self.cluster.ckb_nodes[0].getClient().get_transaction(tx_hash)
        transaction = tx['transaction']
        tx_hash = transaction['hash']
        del transaction['hash']
        light_tx_hash = self.ckb_light_node_0_2_5.getClient().send_transaction(transaction)

        assert tx_hash == light_tx_hash

    @parameterized.expand(success_files)
    def test_06_ckb_light_client_deploy_and_invoke_contract(self, path):
        self.cluster.ckb_nodes[0].stop_miner()
        self.deploy_and_invoke(self.Config.MINER_PRIVATE_1, path, self.cluster.ckb_nodes[0])

    # def test_07_ckb_light_client_deploy_and_invoke_contract(self):
    #     self.deploy_and_invoke(self.Config.MINER_PRIVATE_1, f"{get_project_root()}/source/contract/test_cases/spawn_demo", self.cluster.ckb_nodes[0])

    def deploy_and_invoke(self, account, path, node, try_count=5):
        if try_count < 0:
            raise Exception("try out of times")
        try:
            deploy_hash = self.Contract.deploy_ckb_contract(account,
                                                            path,
                                                            enable_type_id=True,
                                                            api_url=node.getClient().url)
            self.Miner.miner_until_tx_committed(node, deploy_hash)
            time.sleep(1)
            self.ckb_light_node_0_2_5.getClient().fetch_transaction(deploy_hash)
            self.Node.wait_light_sync_height(self.ckb_light_node_0_2_5, node.getClient().get_tip_block_number(), 100)
            time.sleep(10)
            invoke_hash = self.Contract.invoke_ckb_contract(account_private=account,
                                                            contract_out_point_tx_hash=deploy_hash,
                                                            contract_out_point_tx_index=0,
                                                            type_script_arg="0x02", data="0x1234",
                                                            hash_type="type",
                                                            api_url=node.getClient().url)
            tx = node.getClient().get_transaction(invoke_hash)
            transaction = tx['transaction']
            tx_hash = transaction['hash']
            del transaction['hash']
            light_tx_hash = self.ckb_light_node_0_2_5.getClient().send_transaction(transaction)
            assert tx_hash == light_tx_hash
            return invoke_hash
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
