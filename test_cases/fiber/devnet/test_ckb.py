import time

from framework.basic import CkbTest
from framework.helper.udt_contract import UdtContract
from framework.test_fiber import Fiber, FiberConfigPath
from framework.util import generate_random_preimage


class TestFiber(CkbTest):

    @classmethod
    def setup_class(cls):
        account = cls.Ckb_cli.util_key_info_by_private_key(cls.Config.ACCOUNT_PRIVATE_1)
        cls.node = cls.CkbNode.init_dev_by_port(
            cls.CkbNodeConfigPath.CURRENT_FIBER, "contract/node", 8114, 8115
        )
        # cls.node.prepare()
        # cls.node.start()
        # cls.Miner.make_tip_height_number(cls.node, 20)
        # # deploy xudt
        # udtContract = UdtContract()
        # udtContract.deploy(cls.Config.ACCOUNT_PRIVATE_2, cls.node)
        # deploy_hash, deploy_index = udtContract.get_deploy_hash_and_index()
        # # issue
        # invoke_arg, invoke_data = udtContract.issue(account["lock_arg"], 1000 * 100000000)
        # tx_hash = cls.Contract.invoke_ckb_contract(
        #     account_private=cls.Config.ACCOUNT_PRIVATE_1,
        #     contract_out_point_tx_hash=deploy_hash,
        #     contract_out_point_tx_index=deploy_index,
        #     type_script_arg=invoke_arg,
        #     hash_type="type",
        #     data=invoke_data,
        #     fee=1000,
        #     api_url=cls.node.getClient().url,
        #     cell_deps=[],
        #     input_cells=[],
        #     output_lock_arg=account["lock_arg"],
        # )
        # cls.Miner.miner_until_tx_committed(cls.node, tx_hash)
        # cls.node.start_miner()

    def test_ckbdata(self):
        pass

    def test_udt(self):
        """
        1. 建立 udt channel
        2. 转账
        3. close channel
        4. 检查余额
        Returns:

        """
        # open chanel for fiber
        tx = self.node.getClient().get_transaction(
            "0x64a984b818dd162f75f77d223977ff9a509c21f230b99f65c4887f4c2b1c43f2"
        )
        print(tx)
        block = self.node.getClient().get_block_by_number("0x0")
        print(block)

    def test_ckb(self):
        """
        1. 建立 ckb channel
        2. 转账
        3. close channel
        4. 检查余额
        Returns:
        """
