import json

from framework.basic import CkbTest


class TestCkbCliSupport110(CkbTest):

    @classmethod
    def setup_class(cls):
        cls.node = cls.CkbNode.init_dev_by_port(cls.CkbNodeConfigPath.CURRENT_TEST, "ckb_cli/node", 8314, 8315)
        cls.node.prepare()
        cls.node.start()
        cls.Miner.make_tip_height_number(cls.node, 20)

    @classmethod
    def teardown_class(cls):
        print("stop node and clean")
        cls.node.stop()
        cls.node.clean()

    def test_01_version(self):
        ckb_cli_version = self.Ckb_cli.version()
        assert "ckb-cli" in ckb_cli_version, "{ckb_cli_version} not contains ckb-cli".format(
            ckb_cli_version=ckb_cli_version)

    def test_02_estimate_cycles(self):
        """
        estimate_cycles cellbase tx
        - return : 0
        """
        block_number = self.node.getClient().get_tip_block_number()
        block = self.node.getClient().get_block_by_number(hex(block_number))
        # cast TransactionView to Transaction
        del block['transactions'][0]['hash']

        with open("/tmp/tmp.json", 'w') as tmp_file:
            tmp_file.write(json.dumps(block['transactions'][0]))
        result = self.Ckb_cli.estimate_cycles("/tmp/tmp.json",
                                              api_url=self.node.getClient().url)
        assert result == 0

    def test_03_get_transaction_and_witness_proof(self):
        """
        get_transaction_and_witness_proof cellbase tx
        Returns: block_hash which transactions in the block with this hash

        """
        block_number = self.node.getClient().get_tip_block_number()
        block = self.node.getClient().get_block_by_number(hex(block_number))
        cellbase_tx_hash = str(block['transactions'][0]['hash'])
        cellbase_block_hash = block['header']['hash']
        result = self.Ckb_cli.get_transaction_and_witness_proof(tx_hashes=cellbase_tx_hash,
                                                                block_hash=None,
                                                                api_url=self.node.getClient().url)
        assert result['block_hash'] == cellbase_block_hash

    def test_04_verify_transaction_and_witness_proof(self):
        """
        verify_transaction_and_witness_proof cellbase tx_proof
        Returns: cellbase transaction hashes it commits to.

        """
        block_number = self.node.getClient().get_tip_block_number()
        block = self.node.getClient().get_block_by_number(hex(block_number))
        tx_proof = self.node.getClient().get_transaction_and_witness_proof(tx_hashes=[block['transactions'][0]['hash']])
        with open("/tmp/tmp.json", 'w') as tmp_file:
            print(f"tx_proof:{tx_proof}")
            tmp_file.write(json.dumps(tx_proof))
        result = self.Ckb_cli.verify_transaction_and_witness_proof("/tmp/tmp.json", api_url=self.node.getClient().url)
        assert result == block['transactions'][0]['hash']

    def test_05_get_block_with_cycles(self):
        """
        get_block_with_cycles for cellbase
        Returns:cycles: []

        """
        block_number = self.node.getClient().get_tip_block_number()
        block = self.node.getClient().get_block_by_number(hex(block_number))
        cellbase_block_hash = block['header']['hash']
        result = self.Ckb_cli.get_block(cellbase_block_hash, with_cycles=True, api_url=self.node.getClient().url)
        assert result == '[]'

    def test_06_get_block_by_number_with_cycles(self):
        """
        get_block_by_number_with_cycles for cellbase
        Returns:cycles: []

        """
        block_number = self.node.getClient().get_tip_block_number()
        result = self.Ckb_cli.get_block_by_number(block_number, with_cycles=True, api_url=self.node.getClient().url)
        assert result == '[]'

    def test_07_get_consensus(self):
        """
        get_consensus
        Returns:hardfork_features includes 0048 && 0049

        """
        hardfork_features = self.Ckb_cli.get_consensus(api_url=self.node.getClient().url)
        assert any(
            feature.get('rfc') == '0048' for sublist in hardfork_features for feature in sublist), "不包含 RFC 协议 0048"
        assert any(
            feature.get('rfc') == '0049' for sublist in hardfork_features for feature in sublist), "不包含 RFC 协议 0049"

    def test_08_get_deployments_info(self):
        """
        get_deployments_info
        Returns:deployments::light_client::state

        """
        result = self.Ckb_cli.get_deployments_info(api_url=self.node.getClient().url)
        assert result["light_client"]["state"] == 'active'
