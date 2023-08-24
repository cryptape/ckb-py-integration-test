import time

from framework.helper.node import wait_node_height
from framework.test_node import CkbNodeConfigPath, CkbNode
from framework.util import run_command, get_project_root

# use ckb0.110.1-rc1: generate DaoLockSizeMismatch tx in softfork before and after
DATA_ERROR_TAT = f"{get_project_root()}/source/data/data.err.tar.gz"


class TestSyncDaoLockSizeMismatch:

    @classmethod
    def setup_class(cls):
        node1 = CkbNode.init_dev_by_port(CkbNodeConfigPath.V110_MAIN, "tx_pool_test/node1", 8114,
                                         8227)
        node2 = CkbNode.init_dev_by_port(CkbNodeConfigPath.CURRENT_MAIN, "tx_pool_test/node2", 8112,
                                         8228)
        cls.node1 = node1
        cls.node2 = node2
        node1.prepare()
        node2.prepare()
        tar_file(DATA_ERROR_TAT, node1.ckb_dir)
        node1.start()
        node2.start()
        node1.start_miner()
        node1.connected(node2)

    @classmethod
    def teardown_class(cls):
        print("\nTeardown TestClass1")
        cls.node1.stop()
        cls.node1.clean()
        cls.node2.stop()
        cls.node2.clean()

    def test_01_sync(self):
        """
        can't sync DaoLockSizeMismatch tx after softFork active
        6000 block contains DaoLockSizeMismatch tx
        10006 block contains DaoLockSizeMismatch tx
        1. can sync 6000 block
            tip block num > 6000
        2. can't sync 8669 block
            tip block == 8668
        Returns:
        """
        wait_node_height(self.node2, 8668, 120)
        block_num = self.node2.getClient().get_tip_block_number()
        assert block_num == 8668
        time.sleep(10)
        block_num = self.node2.getClient().get_tip_block_number()
        assert block_num == 8668


def tar_file(src_tar, dec_data):
    run_command(f"tar -xvf {src_tar} -C {dec_data}")
