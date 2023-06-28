from framework.config import ACCOUNT_PRIVATE_2, ALWAYS_SUCCESS_CONTRACT_PATH, ACCOUNT_PRIVATE_1, MINER_PRIVATE_1
from framework.helper.contract import deploy_ckb_contract, get_ckb_contract_codehash, invoke_ckb_contract
from framework.helper.miner import miner_until_tx_committed, make_tip_height_number
from framework.test_node import CkbNodeConfigPath, CkbNode


class TestHelperContract:

    @classmethod
    def setup_class(cls):
        cls.node = CkbNode.init_dev_by_port(CkbNodeConfigPath.CURRENT_TEST, "helper/contract/node", 8114, 8115)
        cls.node.prepare()
        cls.node.start()

        make_tip_height_number(cls.node, 100)
        # deploy `anyone_can_pay` contract
        cls.always_success_deploy_hash = deploy_ckb_contract(ACCOUNT_PRIVATE_2,
                                                             ALWAYS_SUCCESS_CONTRACT_PATH,
                                                             enable_type_id=True,
                                                             api_url=cls.node.getClient().url)
        miner_until_tx_committed(cls.node, cls.always_success_deploy_hash)

    @classmethod
    def teardown_class(cls):
        cls.node.stop()
        cls.node.clean()

    def test_get_deploy_data_contract_hash(self):
        code_hash = get_ckb_contract_codehash(self.always_success_deploy_hash, 0, False,
                                              self.node.getClient().url)
        assert code_hash == "0x28e83a1277d48add8e72fadaa9248559e1b632bab2bd60b27955ebc4c03800a5"

    def test_get_deploy_type_contract_hash(self):
        get_ckb_contract_codehash(self.always_success_deploy_hash, 0, True,
                                  self.node.getClient().url)
        # assert code_hash == "0xc68ad51e90b6cd00a93815b4dab30b2568f0543b11b5632f1a331ff1b4b0963a"

    def test_invoke_contract_use_type(self):
        code_hash = get_ckb_contract_codehash(self.always_success_deploy_hash, 0, True,
                                              self.node.getClient().url)
        invoke_hash = invoke_ckb_contract(account_private=MINER_PRIVATE_1,
                                          contract_out_point_tx_hash=self.always_success_deploy_hash,
                                          contract_out_point_tx_index=0,
                                          type_script_arg="0x02", data="0x1234",
                                          hash_type="type",
                                          api_url=self.node.getClient().url)
        miner_until_tx_committed(self.node, invoke_hash)
        tx_response = self.node.getClient().get_transaction(invoke_hash)
        assert tx_response["transaction"]["outputs"][0]["type"]["code_hash"] == code_hash
        assert tx_response["transaction"]["outputs"][0]["type"]["hash_type"] == "type"
        assert tx_response["transaction"]["outputs"][0]["type"]["args"] == "0x02"

    def test_invoke_contract_use_data(self):
        code_hash = get_ckb_contract_codehash(self.always_success_deploy_hash, 0, False,
                                              self.node.getClient().url)

        invoke_hash = invoke_ckb_contract(account_private=MINER_PRIVATE_1,
                                          contract_out_point_tx_hash=self.always_success_deploy_hash,
                                          contract_out_point_tx_index=0,
                                          type_script_arg="0x02", data="0x1234",
                                          hash_type="data",
                                          api_url=self.node.getClient().url)
        miner_until_tx_committed(self.node, invoke_hash)
        tx_response = self.node.getClient().get_transaction(invoke_hash)
        assert tx_response["transaction"]["outputs"][0]["type"]["code_hash"] == code_hash
        assert tx_response["transaction"]["outputs"][0]["type"]["hash_type"] == "data"
        assert tx_response["transaction"]["outputs"][0]["type"]["args"] == "0x02"

    def test_invoke_contract_use_data1(self):
        code_hash = get_ckb_contract_codehash(self.always_success_deploy_hash, 0, False,
                                              self.node.getClient().url)

        invoke_hash = invoke_ckb_contract(account_private=MINER_PRIVATE_1,
                                          contract_out_point_tx_hash=self.always_success_deploy_hash,
                                          contract_out_point_tx_index=0,
                                          type_script_arg="0x02", data="0x1234",
                                          hash_type="data1",
                                          api_url=self.node.getClient().url)
        miner_until_tx_committed(self.node, invoke_hash)
        tx_response = self.node.getClient().get_transaction(invoke_hash)
        assert tx_response["transaction"]["outputs"][0]["type"]["code_hash"] == code_hash
        assert tx_response["transaction"]["outputs"][0]["type"]["hash_type"] == "data1"
        assert tx_response["transaction"]["outputs"][0]["type"]["args"] == "0x02"
