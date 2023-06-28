from framework.config import ACCOUNT_PRIVATE_1, ACCOUNT_PRIVATE_2
from framework.helper.ckb_cli import version, util_key_info_by_private_key, get_deploy_toml_config, wallet_get_capacity, \
    wallet_get_live_cells, wallet_transfer_by_private_key
from framework.helper.miner import miner_until_tx_committed, make_tip_height_number
from framework.test_node import CkbNode, CkbNodeConfigPath


class TestCkbCli:

    @classmethod
    def setup_class(cls):
        cls.node = CkbNode.init_dev_by_port(CkbNodeConfigPath.CURRENT_TEST, "ckb_cli/node", 8314, 8315)
        cls.node.prepare()
        cls.node.start()
        make_tip_height_number(cls.node,20)

    @classmethod
    def teardown_class(cls):
        print("stop node and clean")
        cls.node.stop()
        cls.node.clean()

    def test_01_version(self):
        ckb_cli_version = version()
        assert "ckb-cli" in ckb_cli_version, "{ckb_cli_version} not contains ckb-cli".format(
            ckb_cli_version=ckb_cli_version)

    def test_util_key_info_by_private_key(self):
        account1 = util_key_info_by_private_key(ACCOUNT_PRIVATE_1)
        assert "ckt1qzda0cr08m85hc8jlnfp3zer7xulejywt49kt2rr0vthywaa50xwsqwgx292hnvmn68xf779vmzrshpmm6epn4c0cgwga" == \
               account1['address']['testnet']

    def test_get_deploy_toml(self):
        config_toml_str = get_deploy_toml_config(ACCOUNT_PRIVATE_2, "/tmp/path", True)
        assert "0x470dcdc5e44064909650113a274b3b36aecb6dc7" in config_toml_str

    def test_get_account_balance(self):
        account1 = util_key_info_by_private_key(ACCOUNT_PRIVATE_1)
        ckb_address = account1['address']['testnet']
        account_capacity = wallet_get_capacity(ckb_address, self.node.getClient().url)
        assert account_capacity > 10000000000.0

    def test_get_account_live_cells(self):
        account1 = util_key_info_by_private_key(ACCOUNT_PRIVATE_1)
        ckb_address = account1['address']['testnet']
        live_cells = wallet_get_live_cells(ckb_address, self.node.getClient().url)
        assert len(live_cells["live_cells"]) > 0

    def test_account1_transfer_account2(self):
        transfer_balance = 100

        account2 = util_key_info_by_private_key(ACCOUNT_PRIVATE_2)
        ckb_address = account2['address']['testnet']

        before_transfer_capacity = wallet_get_capacity(ckb_address, self.node.getClient().url)

        # account 1 transfer 100 to account 2
        tx_hash = wallet_transfer_by_private_key(ACCOUNT_PRIVATE_1, ckb_address, transfer_balance,
                                                 api_url=self.node.getClient().url)

        # wait transfer tx committed
        miner_until_tx_committed(self.node, tx_hash)

        # check balance is right
        after_transfer_capacity = wallet_get_capacity(ckb_address, self.node.getClient().url)
        assert after_transfer_capacity - transfer_balance == before_transfer_capacity
