import json

from framework.helper.ckb_cli import version, estimate_cycles
from framework.helper.miner import make_tip_height_number
from framework.test_node import CkbNode, CkbNodeConfigPath


class TestCkbCliSupport110:

    @classmethod
    def setup_class(cls):
        cls.node = CkbNode.init_dev_by_port(CkbNodeConfigPath.CURRENT_TEST, "ckb_cli/node", 8314, 8315)
        cls.node.prepare()
        cls.node.start()
        make_tip_height_number(cls.node, 20)

    @classmethod
    def teardown_class(cls):
        print("stop node and clean")
        cls.node.stop()
        cls.node.clean()

    def test_01_version(self):
        ckb_cli_version = version()
        assert "ckb-cli" in ckb_cli_version, "{ckb_cli_version} not contains ckb-cli".format(
            ckb_cli_version=ckb_cli_version)

    def test_estimate_cycles(self):
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
        result = estimate_cycles("/tmp/tmp.json",
                                 api_url=self.node.getClient().url)
        assert result == 0
