from framework.basic import CkbTest
from framework.helper.udt_contract import UdtContract


class UdtTest(CkbTest):

    @classmethod
    def setup_class(cls):
        cls.node = cls.CkbNode.init_dev_by_port(
            cls.CkbNodeConfigPath.CURRENT_TEST, "contract/node", 8116, 8115
        )
        cls.node.prepare()
        cls.node.start()
        cls.Miner.make_tip_height_number(cls.node, 2000)

    @classmethod
    def teardown_class(cls):
        pass
        cls.node.stop()
        cls.node.clean()

    def test_01111(self):
        account = self.Ckb_cli.util_key_info_by_private_key(self.Config.ACCOUNT_PRIVATE_1)
        account1 = self.Ckb_cli.util_key_info_by_private_key(self.Config.ACCOUNT_PRIVATE_2)
        account2 = self.Ckb_cli.util_key_info_by_private_key(self.Config.MINER_PRIVATE_1)

        # deploy
        udtContract = UdtContract()
        udtContract.deploy(self.Config.ACCOUNT_PRIVATE_1, self.node)
        deploy_hash, deploy_index = udtContract.get_deploy_hash_and_index()
        # issue
        invoke_arg, invoke_data = udtContract.issue(account1['lock_arg'], 100000)
        tx_hash = self.Contract.invoke_ckb_contract(
            account_private=self.Config.ACCOUNT_PRIVATE_2,
            contract_out_point_tx_hash=deploy_hash,
            contract_out_point_tx_index=deploy_index,
            type_script_arg=invoke_arg,
            hash_type="type",
            data=invoke_data,
            fee=1000,
            api_url=self.node.getClient().url,
            cell_deps=[],
            input_cells=[],
            output_lock_arg=account2['lock_arg']
        )
        ret = self.node.getClient().get_transaction(tx_hash)
        print("ret:", ret)
        self.Miner.miner_until_tx_committed(self.node, tx_hash)
        result = udtContract.list_cell(self.node.getClient(), account1['lock_arg'],
                                       account2['lock_arg'])
        print("result ret:", result)
        # transfer
        invoke_arg, invoke_data = udtContract.transfer(account1['lock_arg'], 100000)
        tx_hash = self.Contract.invoke_ckb_contract(
            account_private=self.Config.MINER_PRIVATE_1,
            contract_out_point_tx_hash=deploy_hash,
            contract_out_point_tx_index=deploy_index,
            type_script_arg=invoke_arg,
            hash_type="type",
            data=invoke_data,
            fee=1000,
            api_url=self.node.getClient().url,
            cell_deps=[],
            input_cells=[result[0]['input_cell']],
            output_lock_arg="0x0000000000000000000000000000000000000000"
        )
        self.Miner.miner_until_tx_committed(self.node, tx_hash)
        # query
        result = udtContract.list_cell(self.node.getClient(), account1['lock_arg'],
                                       "0x0000000000000000000000000000000000000000")
        print("result:", result)
        assert result[0]['balance'] == 100000
