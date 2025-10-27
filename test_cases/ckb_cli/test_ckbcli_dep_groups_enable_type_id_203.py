from framework.basic import CkbTest


class TestCkbCliMultisig203(CkbTest):

    @classmethod
    def setup_class(cls):
        """
        1. start 1 ckb node in tmp/ckb_cli/node dir
        2. miner 2 block
        Returns:

        """
        # 1. start 1 ckb node in tmp/ckb_cli/node dir
        cls.node = cls.CkbNode.init_dev_by_port(
            cls.CkbNodeConfigPath.CURRENT_TEST, "ckb_cli/node", 8314, 8315
        )
        cls.node.prepare()
        cls.node.start()
        # 2. miner 2 block
        cls.Miner.make_tip_height_number(cls.node, 2)

    @classmethod
    def teardown_class(cls):
        """
        1. stop ckb node
        2. clean ckb node tmp dir
        Returns:

        """
        print("stop node and clean")
        cls.node.stop()
        cls.node.clean()

    def test_01_dep_groups_enable_type_id_true(self):
        # 1. deploy contract return deploy tx hash
        dep_group_tx_hash = self.Contract.deploy_ckb_contract(
            self.Config.ACCOUNT_PRIVATE_2,
            self.Config.ALWAYS_SUCCESS_CONTRACT_PATH,
            enable_type_id=True,
            dep_groups_enable_type_id=True,
            return_tx="dep_group_tx",
            api_url=self.node.getClient().url,
        )
        # 2. miner until deploy contrct tx hash
        tx_response = self.Miner.miner_until_tx_committed(self.node, dep_group_tx_hash)
        output = tx_response["transaction"]["outputs"][0]
        # 3. check hash_type
        output_type = output.get("type")
        assert (
            output_type is not None
        ), "Failed: Output does not contain a 'type' field."

    def test_02_dep_groups_enable_type_id_false(self):
        # 1. deploy contract return deploy tx hash
        dep_group_tx_hash = self.Contract.deploy_ckb_contract(
            self.Config.ACCOUNT_PRIVATE_2,
            self.Config.ALWAYS_SUCCESS_CONTRACT_PATH,
            enable_type_id=True,
            dep_groups_enable_type_id=False,
            return_tx="dep_group_tx",
            api_url=self.node.getClient().url,
        )
        # 2. miner until deploy contrct tx hash
        tx_response = self.Miner.miner_until_tx_committed(self.node, dep_group_tx_hash)
        output = tx_response["transaction"]["outputs"][0]
        # 3. check hash_type
        assert (
            output.get("type") is None
        ), f"Failed: type field should be None, got {output.get('type')}"

    def test_03_dep_groups_enable_type_id_old(self):
        # 1. deploy contract return deploy tx hash
        dep_group_tx_hash = self.Contract.deploy_ckb_contract(
            self.Config.ACCOUNT_PRIVATE_2,
            self.Config.ALWAYS_SUCCESS_CONTRACT_PATH,
            enable_type_id=True,
            dep_groups_enable_type_id="old",
            return_tx="dep_group_tx",
            api_url=self.node.getClient().url,
        )
        # 2. miner until deploy contrct tx hash
        tx_response = self.Miner.miner_until_tx_committed(self.node, dep_group_tx_hash)
        output = tx_response["transaction"]["outputs"][0]
        # 3. check hash_type
        assert (
            output.get("type") is None
        ), f"Failed: type field should be None, got {output.get('type')}"
