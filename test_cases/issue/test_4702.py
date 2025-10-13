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


def get_failed_files():
    project_root = get_project_root()
    files = get_all_files(f"{get_project_root()}/source/contract/test_cases")

    files_list = [
        "exec_with_exec",
    ]
    # return [s for s in files if not any(s.endswith(suffix) for suffix in files_list)]
    return [f"{project_root}/source/contract/test_cases/{x}" for x in files_list]


class Test4702(CkbTest):
    failed_files = get_failed_files()

    @classmethod
    def setup_class(cls):
        """
        1.启动node1和node2两个节点
        """
        cls.local_node = cls.CkbNode.init_dev_by_port(
            cls.CkbNodeConfigPath.CURRENT_TEST, "tx_pool/node1", 8120, 8225
        )
        cls.remote_node = cls.CkbNode.init_dev_by_port(
            cls.CkbNodeConfigPath.CURRENT_TEST, "tx_pool/node2", 8121, 8226
        )
        cls.cluster = cls.Cluster([cls.local_node, cls.remote_node])
        cls.cluster.prepare_all_nodes()
        cls.cluster.start_all_nodes()
        cls.Miner.make_tip_height_number(cls.local_node, 200)

    @classmethod
    def teardown_class(cls):
        # cls.cluster.stop_all_nodes()
        # cls.cluster.clean_all_nodes()
        pass
    @parameterized.expand(failed_files)
    def test_4702(self, path):
        """
        2.首先node1和node2两个节点建立p2p连接
        3.然后通过node1将包含这个大交易的区块上链，node2 同步到这个区块这个大交易 p2p 广播给 node2
        4.接着node2的ckb-vm执行这个交易的过程中，发送 ctrl-c 给node2. 然后 node2 执行交易就会报错
        5.预期的行为是node2不能ban掉remote的node1节点以及node2重启后日志里不会提示vm internal error的错误
        """

        # 通过node1将包含这个大交易的区块上链，node2 同步到这个区块这个大交易 p2p 广播给 node2
        invoke_hash = self.deploy_and_invoke(
            self.Config.MINER_PRIVATE_1, path, self.local_node
        )
        self.Miner.miner_until_tx_committed(self.local_node, invoke_hash)
        for i in range(0, 20):
            self.Miner.miner_with_version(self.local_node, "0x0")
        tx = self.local_node.getClient().get_transaction(invoke_hash)
        block_number = tx["tx_status"]["block_number"]
        # node1和node2两个节点建立p2p连接
        self.cluster.connected_all_nodes()
        self.Node.wait_cluster_height(self.cluster, int(block_number, 16) - 1, 200)
        tip = self.remote_node.getClient().get_tip_block_number()
        assert tip == int(block_number, 16) - 1
        # 接着node2的ckb-vm执行这个交易的过程中，发送 ctrl-c 给node2. 然后 node2 执行交易就会报错
        self.remote_node.stop()
        self.remote_node.rmLockFile()
        self.remote_node.start()
        print(f"ban info:{self.remote_node.getClient().get_banned_addresses()}")
        # 预期的行为是node2不能ban掉remote的node1节点以及node2重启后日志里不会提示vm internal error的错误
        assert self.remote_node.getClient().get_banned_addresses() == []

    def deploy_and_invoke(self, account, path, node, try_count=5):
        if try_count < 0:
            raise Exception("try out of times")
        try:
            deploy_hash = self.Contract.deploy_ckb_contract(
                account, path, enable_type_id=True, api_url=node.getClient().url
            )
            self.Miner.miner_until_tx_committed(node, deploy_hash)
            time.sleep(1)
            invoke_hash = self.Contract.invoke_ckb_contract(
                account_private=account,
                contract_out_point_tx_hash=deploy_hash,
                contract_out_point_tx_index=0,
                type_script_arg="0x02",
                data="0x1234",
                hash_type="type",
                api_url=node.getClient().url,
            )

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
