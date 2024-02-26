# https://github.com/nervosnetwork/ckb/pull/4111
import time

import pytest

from framework.basic import CkbTest
from framework.util import get_project_root


class Test4111(CkbTest):

    @classmethod
    def setup_class(cls):
        node1 = cls.CkbNode.init_dev_by_port(cls.CkbNodeConfigPath.CURRENT_TEST, "issue/node1", 8914,
                                             8927)
        cls.node = node1
        node1.prepare(
            other_ckb_config={'ckb_logger_filter': 'debug'}
        )
        node1.start()
        cls.Miner.make_tip_height_number(cls.node, 400)

    @classmethod
    def teardown_class(cls):
        print("\nTeardown TestClass1")
        cls.node.stop()
        cls.node.clean()

    def test_issue_4111(self):
        """
        build tx that output cap > input cap
        expected contains (outputs capacity) > (inputs capacity) msg
        but current ckb-cli not return error.data msg :
        Returns: error:Malformed Overflow transaction
        """
        with pytest.raises(Exception) as exc_info:
            self.deploy_and_invoke(self.Config.MINER_PRIVATE_1,
                                   f"{get_project_root()}/source/contract/always_success",
                                   self.node, 1)
        expected_error_message = "Malformed Overflow transaction"
        print("exc_info.value.args[0]:", exc_info.value.args[0])
        assert expected_error_message in exc_info.value.args[0], \
            f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

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
            invoke_hash = self.Contract.invoke_ckb_contract(account_private=account,
                                                            contract_out_point_tx_hash=deploy_hash,
                                                            contract_out_point_tx_index=0,
                                                            type_script_arg="0x02", data="0x1234",
                                                            hash_type="type",
                                                            api_url=node.getClient().url, fee=-100)
            return invoke_hash
        except Exception as e:
            if "Resolve failed Dead" in e.args[0]:
                try_count -= 1
                time.sleep(3)
                return self.deploy_and_invoke(account, path, node, try_count)
            raise Exception(e.args[0])
