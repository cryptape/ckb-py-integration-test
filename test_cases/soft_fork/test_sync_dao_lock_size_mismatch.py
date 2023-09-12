import time

from framework.basic import CkbTest
from framework.util import run_command, get_project_root

# use ckb0.110.1-rc1: generate DaoLockSizeMismatch tx in softfork before and after
DATA_ERROR_TAT = f"{get_project_root()}/source/data/data.err.tar.gz"


class TestSyncDaoLockSizeMismatch(CkbTest):

    def setup_method(self, method):
        pass

    def teardown_method(self, method):
        print("\nTearing down method", method.__name__)
        self.node1.stop_miner()
        self.node1.stop()
        self.node1.clean()
        self.node2.stop()
        self.node2.clean()

    def test_01_sync_dao_out_of_starting_block_limiting_dao_withdrawing_lock(self):
        """
        can sync DaoLockSizeMismatch tx
         - after softFork active
         - starting_block_limiting_dao_withdrawing_lock > dao deposit tx block number

        6000 block contains DaoLockSizeMismatch tx
        5495 block contains dao deposit tx
        8669 block contains DaoLockSizeMismatch tx use 5495 dao deposit tx
        1. can sync 6000 block
            tip block num > 6000
        2. can't sync 8669 block
            tip block == 8668
        Returns:
        """

        node1 = self.CkbNode.init_dev_by_port(self.CkbNodeConfigPath.V110_MAIN, "tx_pool_test/node1", 8114, 8227)
        node2 = self.CkbNode.init_dev_by_port(self.CkbNodeConfigPath.CURRENT_MAIN, "tx_pool_test/node2", 8112, 8228)
        self.node1 = node1
        self.node2 = node2
        node1.prepare(other_ckb_spec_config={"starting_block_limiting_dao_withdrawing_lock": "5495"})
        node2.prepare(other_ckb_spec_config={"starting_block_limiting_dao_withdrawing_lock": "5495"})
        tar_file(DATA_ERROR_TAT, node1.ckb_dir)
        node1.start()
        node2.start()
        node1.start_miner()
        node1.connected(node2)

        self.Node.wait_node_height(self.node2, 8669, 120)

    def test_02_sync_dao_in_starting_block_limiting_dao_withdrawing_lock(self):
        """
        can't sync DaoLockSizeMismatch tx
        - after softFork active
        - starting_block_limiting_dao_withdrawing_lock <= dao deposit tx block number

        6000 block contains DaoLockSizeMismatch tx
        8669 block contains DaoLockSizeMismatch tx
        1. can sync 6000 block
            tip block num > 6000
        2. can't sync 8669 block
            tip block == 8668
        Returns:
        """
        node1 = self.CkbNode.init_dev_by_port(self.CkbNodeConfigPath.V110_MAIN, "tx_pool_test/node1", 8114, 8227)
        node2 = self.CkbNode.init_dev_by_port(self.CkbNodeConfigPath.CURRENT_MAIN, "tx_pool_test/node2", 8112, 8228)
        self.node1 = node1
        self.node2 = node2
        node1.prepare(other_ckb_spec_config={"starting_block_limiting_dao_withdrawing_lock": "5494"})
        node2.prepare(other_ckb_spec_config={"starting_block_limiting_dao_withdrawing_lock": "5494"})
        tar_file(DATA_ERROR_TAT, node1.ckb_dir)
        node1.start()
        node2.start()
        node1.start_miner()
        node1.connected(node2)

        self.Node.wait_node_height(self.node2, 8668, 120)
        block_num = self.node2.getClient().get_tip_block_number()
        assert block_num == 8668
        time.sleep(10)
        block_num = self.node2.getClient().get_tip_block_number()
        assert block_num == 8668

    def test_03_sync_dao_lock_size_mismatch_before_soft_fork(self):
        """
        can sync DaoLockSizeMismatch tx
        - before softFork active
        6000 block contains DaoLockSizeMismatch tx
        1. can sync 6000 block
            tip block num > 6000
        2. can't sync 8669 block(DaoLockSizeMismatch tx)
            tip block == 8668
        Returns:
        """
        node1 = self.CkbNode.init_dev_by_port(self.CkbNodeConfigPath.V110_MAIN, "tx_pool_test/node1", 8114, 8227)
        node2 = self.CkbNode.init_dev_by_port(self.CkbNodeConfigPath.CURRENT_MAIN, "tx_pool_test/node2", 8112, 8228)
        self.node1 = node1
        self.node2 = node2
        node1.prepare(other_ckb_spec_config={"starting_block_limiting_dao_withdrawing_lock": "10"})
        node2.prepare(other_ckb_spec_config={"starting_block_limiting_dao_withdrawing_lock": "10"})
        tar_file(DATA_ERROR_TAT, node1.ckb_dir)
        node1.start()
        node2.start()
        node1.start_miner()
        node1.connected(node2)

        self.Node.wait_node_height(self.node2, 8668, 120)
        block_num = self.node2.getClient().get_tip_block_number()
        assert block_num == 8668
        time.sleep(10)
        block_num = self.node2.getClient().get_tip_block_number()
        assert block_num == 8668


def tar_file(src_tar, dec_data):
    run_command(f"tar -xvf {src_tar} -C {dec_data}")
