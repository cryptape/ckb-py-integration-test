import pytest

from framework.config import MINER_PRIVATE_1
from framework.helper.ckb_cli import wallet_transfer_by_private_key, util_key_info_by_private_key
from framework.helper.miner import make_tip_height_number
from framework.test_node import CkbNode, CkbNodeConfigPath


class TestRBFConfig:
    @classmethod
    def setup_class(cls):
        cls.node = CkbNode.init_dev_by_port(CkbNodeConfigPath.CURRENT_TEST, "tx_pool/node1", 8120,
                                            8225)
        cls.node.prepare(other_ckb_config={"ckb_tx_pool_min_rbf_rate": "800"})
        cls.node.start()
        make_tip_height_number(cls.node, 30)

    @classmethod
    def teardown_class(cls):
        cls.node.stop()
        cls.node.clean()

    def test_transaction_replacement_disabled_failure(self):
        """
        Disabling RBF (Replace-By-Fee) feature, transaction replacement fails.
        1. starting the node, modify ckb.toml with min_rbf_rate = 800 < min_fee_rate.
            node starts successfully.
        2. send tx use same input cell
            ERROR:  TransactionFailedToResolve: Resolve failed Dead
        :return:
        """

        account = util_key_info_by_private_key(MINER_PRIVATE_1)

        wallet_transfer_by_private_key(MINER_PRIVATE_1, account["address"]["testnet"], 100,
                                       self.node.getClient().url, "1500")

        with pytest.raises(Exception) as exc_info:
            wallet_transfer_by_private_key(MINER_PRIVATE_1, account["address"]["testnet"], 200,
                                           self.node.getClient().url, "2000")
        expected_error_message = " TransactionFailedToResolve: Resolve failed Dead"
        assert expected_error_message in exc_info.value.args[0], \
            f"Expected substring '{expected_error_message}' " \
            f"not found in actual string '{exc_info.value.args[0]}'"
