import os
import time

import pytest
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
#     return [s for s in files if not any(s.endswith(suffix) for suffix in files_list)]

def get_successful_files():
    return [
        f"{get_project_root()}/source/contract/test_cases/ckb_get_memory_limit",
        f"{get_project_root()}/source/contract/test_cases/atomic_i32",
        f"{get_project_root()}/source/contract/test_cases/spawn_current_cycles"
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

        cls.ckb_light_node_current = cls.CkbLightClientNode.init_by_nodes(cls.CkbLightClientConfigPath.CURRENT_TEST,
                                                                          cls.cluster.ckb_nodes,
                                                                          "tx_pool_light/node1", 8001)

        cls.ckb_light_node_current.prepare()
        cls.ckb_light_node_current.start()
        account = cls.Ckb_cli.util_key_info_by_private_key(cls.Config.MINER_PRIVATE_1)
        cls.ckb_light_node_current.getClient().set_scripts([{"script": {
            "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8", "hash_type": "type",
            "args": account['lock_arg']}, "script_type": "lock", "block_number": "0x0"}])

        cls.cluster.ckb_nodes[0].start_miner()
        cls.Node.wait_light_sync_height(cls.ckb_light_node_current, 2000, 200)

    @classmethod
    def teardown_class(cls):
        print("\nTeardown TestClass1")
        cls.cluster.stop_all_nodes()
        cls.cluster.clean_all_nodes()
        cls.ckb_light_node_current.stop()
        cls.ckb_light_node_current.clean()

    def test_01_ckb_light_client_0_3_1_link_node(self):

        version = self.CkbLightClientConfigPath.V0_3_1
        ckb_light_node = self.CkbLightClientNode.init_by_nodes(version,
                                                               self.cluster.ckb_nodes,
                                                               "tx_pool_light/node2", 8002)
        ckb_light_node.prepare()
        ckb_light_node.start()
        account = self.Ckb_cli.util_key_info_by_private_key(self.Config.MINER_PRIVATE_1)
        ckb_light_node.getClient().set_scripts([{"script": {
            "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8", "hash_type": "type",
            "args": account['lock_arg']}, "script_type": "lock", "block_number": "0x0"}])
        with pytest.raises(Exception) as exc_info:
            self.Node.wait_light_sync_height(ckb_light_node, 2000, 200)
        expected_error_message = "time out"
        assert expected_error_message in exc_info.value.args[0], \
            f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"
        ckb_light_node.stop()
        ckb_light_node.clean()


    def test_02_ckb_light_client_current_link_node(self):
        """
        1. setScript miner account
            set successful
        2. wait miner script sync
            sync successful
        Returns:

        """
        account = self.Ckb_cli.util_key_info_by_private_key(self.Config.MINER_PRIVATE_1)
        self.ckb_light_node_current.getClient().set_scripts([{"script": {
            "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8", "hash_type": "type",
            "args": account['lock_arg']}, "script_type": "lock", "block_number": "0x0"}])
        self.Node.wait_light_sync_height(self.ckb_light_node_current, 2000, 200)


    def test_03_ckb_light_client_current_set_script_data2(self):
        """
        1. set data2 account
            sync successful
        Returns:

        """
        account = self.Ckb_cli.util_key_info_by_private_key(self.Config.MINER_PRIVATE_1)
        self.ckb_light_node_current.getClient().set_scripts([{"script": {
            "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8", "hash_type": "data2",
            "args": account['lock_arg']}, "script_type": "lock", "block_number": "0x0"}])
        self.Node.wait_light_sync_height(self.ckb_light_node_current, 2000, 200)


    def test_04_ckb_light_client_current_transfer_data2_tx(self):
        """
        1. send data2 tx on the ckb light client
                send successful ,return tx_hash
        Returns:

        """
        account = self.Ckb_cli.util_key_info_by_private_key(self.Config.MINER_PRIVATE_1)
        self.ckb_light_node_current.getClient().set_scripts([{"script": {
            "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8", "hash_type": "type",
            "args": account['lock_arg']}, "script_type": "lock", "block_number": "0x0"}])
        self.Node.wait_light_sync_height(self.ckb_light_node_current, 2000, 200)


        tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(self.Config.MINER_PRIVATE_1,
                                                              "ckt1qp5usrt2syzfjj7acyetk45vj57kp7hq4jfg4ky8e9k7ss6v52neqpqh7xtq0",
                                                              140,
                                                              self.cluster.ckb_nodes[0].client.url)
        tx = self.cluster.ckb_nodes[0].getClient().get_transaction(tx_hash)
        transaction = tx['transaction']
        tx_hash = transaction['hash']
        del transaction['hash']
        light_tx_hash = self.ckb_light_node_current.getClient().send_transaction(transaction)

        assert tx_hash == light_tx_hash


    def test_05_ckb_light_client_current_spawn_contract_use_data2(self):
        """
           1. send spawn tx ( hash type : data2), on the ckb light client
                   send successful ,return tx_hash
           Returns:
        """
        # send rfc50 tx
        self.cluster.ckb_nodes[0].start_miner()
        account = self.Ckb_cli.util_key_info_by_private_key(self.Config.MINER_PRIVATE_1)
        self.ckb_light_node_current.getClient().set_scripts([{"script": {
            "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8", "hash_type": "type",
            "args": account['lock_arg']}, "script_type": "lock", "block_number": "0x0"}])
        self.Node.wait_light_sync_height(self.ckb_light_node_current, 2000, 200)
        self.cluster.ckb_nodes[0].stop_miner()

        code_tx_hash, code_tx_index = self.spawn_contract.get_deploy_hash_and_index()
        invoke_arg, invoke_data = self.spawn_contract.get_arg_and_data("demo")
        tx_hash = self.Contract.invoke_ckb_contract(self.Config.MINER_PRIVATE_1, code_tx_hash, code_tx_index,
                                                    invoke_arg, "data2", invoke_data,
                                                    api_url=self.cluster.ckb_nodes[0].getClient().url)

        self.ckb_light_node_current.getClient().fetch_transaction(code_tx_hash)
        # TODO wait fetch tx succ
        time.sleep(5)
        self.ckb_light_node_current.getClient().fetch_transaction(code_tx_hash)
        tx = self.cluster.ckb_nodes[0].getClient().get_transaction(tx_hash)
        transaction = tx['transaction']
        tx_hash = transaction['hash']
        del transaction['hash']
        light_tx_hash = self.ckb_light_node_current.getClient().send_transaction(transaction)

        assert tx_hash == light_tx_hash


    def test_05_ckb_light_client_current_spawn_contract_use_type(self):
        """
           1. send spawn tx ( hash type : type), on the ckb light client
                   send successful ,return tx_hash
           Returns:
        """
        # send rfc50 tx
        self.cluster.ckb_nodes[0].start_miner()
        account = self.Ckb_cli.util_key_info_by_private_key(self.Config.MINER_PRIVATE_1)
        self.ckb_light_node_current.getClient().set_scripts([{"script": {
            "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8", "hash_type": "type",
            "args": account['lock_arg']}, "script_type": "lock", "block_number": "0x0"}])
        self.Node.wait_light_sync_height(self.ckb_light_node_current, 2000, 200)
        self.cluster.ckb_nodes[0].stop_miner()

        code_tx_hash, code_tx_index = self.spawn_contract.get_deploy_hash_and_index()
        invoke_arg, invoke_data = self.spawn_contract.get_arg_and_data("demo")
        tx_hash = self.Contract.invoke_ckb_contract(self.Config.MINER_PRIVATE_1, code_tx_hash, code_tx_index,
                                                    invoke_arg, "type", invoke_data,
                                                    api_url=self.cluster.ckb_nodes[0].getClient().url)

        self.ckb_light_node_current.getClient().fetch_transaction(code_tx_hash)
        time.sleep(5)
        self.ckb_light_node_current.getClient().fetch_transaction(code_tx_hash)
        tx = self.cluster.ckb_nodes[0].getClient().get_transaction(tx_hash)
        transaction = tx['transaction']
        tx_hash = transaction['hash']
        del transaction['hash']
        light_tx_hash = self.ckb_light_node_current.getClient().send_transaction(transaction)
        assert tx_hash == light_tx_hash

    # @pytest.mark.skip
    # @parameterized.expand(success_files)
    # def test_06_ckb_light_client_deploy_and_invoke_contract(self, path):
    #     self.cluster.ckb_nodes[0].start_miner()
    #     self.deploy_and_invoke(self.Config.MINER_PRIVATE_1, path, self.cluster.ckb_nodes[0])
    #     self.cluster.ckb_nodes[0].start_miner()

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
