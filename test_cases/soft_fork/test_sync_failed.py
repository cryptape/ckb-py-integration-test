import time

from framework.basic import CkbTest
from framework.util import run_command, get_project_root

# use ckb0.110.1-rc1: generate DaoLockSizeMismatch tx in softfork before and after
DATA_ERROR_TAT = f"{get_project_root()}/source/data/data.err.tar.gz"


class TestSyncFailed(CkbTest):

    def teardown_method(self, method):
        super().teardown_method(method)
        print("\nTearing down method", method.__name__)
        self.node1.stop()
        self.node1.clean()

        self.node2.stop()
        self.node2.clean()

        self.node3.stop()
        self.node3.clean()

    def test_sync_other_node_again_after_failed(self):
        """
        can't sync DaoLockSizeMismatch tx
        - after softFork active
        - starting_block_limiting_dao_withdrawing_lock <= dao deposit tx block number
        6000 block contains DaoLockSizeMismatch tx
        8669 block contains DaoLockSizeMismatch tx
        1. can sync 6000 block
            tip block num > 6000
        2. node2 and node3 can't sync 8669 block
            tip block == 8668
        3. node2 miner
        4. node2 restart and miner
        5. node1 stop
        6. link node2 and node3
        7. node3 sync node2 successful

        Returns:
        """
        node1 = self.CkbNode.init_dev_by_port(self.CkbNodeConfigPath.V110_MAIN, "tx_pool_test/node1", 8114, 8227)
        node2 = self.CkbNode.init_dev_by_port(self.CkbNodeConfigPath.CURRENT_MAIN, "tx_pool_test/node2", 8112, 8228)
        node3 = self.CkbNode.init_dev_by_port(self.CkbNodeConfigPath.CURRENT_MAIN, "tx_pool_test/node3", 8113, 8229)
        self.node1 = node1
        self.node2 = node2
        self.node3 = node3
        node1.prepare(other_ckb_spec_config={"starting_block_limiting_dao_withdrawing_lock": "5494"})
        node2.prepare(other_ckb_spec_config={"starting_block_limiting_dao_withdrawing_lock": "5494"})
        node3.prepare(other_ckb_spec_config={"starting_block_limiting_dao_withdrawing_lock": "5494"})
        tar_file(DATA_ERROR_TAT, node1.ckb_dir)
        node1.start()
        node2.start()
        node3.start()
        self.Miner.make_tip_height_number(node1, 15000)
        node1.start_miner()
        node1.connected(node2)
        node1.connected(node3)
        self.Node.wait_node_height(self.node2, 8668, 120)
        self.Node.wait_node_height(self.node3, 8668, 120)
        block_num = self.node2.getClient().get_tip_block_number()
        assert block_num == 8668
        time.sleep(10)
        block_num = self.node2.getClient().get_tip_block_number()
        assert block_num == 8668
        node2_banned_result = node2.getClient().get_banned_addresses()
        node3_banned_result = node3.getClient().get_banned_addresses()
        assert "BlockIsInvalid" in node2_banned_result[0]['ban_reason']
        assert "BlockIsInvalid" in node3_banned_result[0]['ban_reason']
        node1.stop()
        node2.getClient().clear_banned_addresses()
        node3.getClient().clear_banned_addresses()
        self.Miner.make_tip_height_number(node2, 10000)
        node2.restart()
        self.node2.start_miner()
        node2.connected(node3)
        node3.connected(node2)

        self.Node.wait_node_height(self.node2, 10001, 120)
        self.Node.wait_node_height(self.node3, 10001, 120)


def tar_file(src_tar, dec_data):
    run_command(f"tar -xvf {src_tar} -C {dec_data}")
