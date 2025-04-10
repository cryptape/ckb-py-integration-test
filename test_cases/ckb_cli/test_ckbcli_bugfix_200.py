import json

from framework.basic import CkbTest
from framework.rpc import RPCClient


class TestCkbCliRpc200(CkbTest):
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

    def test_01_get_transaction(self):
        """
        1.use ckb-cli to get transaction by its hash
        2.use rpc to get transaction by its hash
        3.compare ckb-cli fee == rpc fee
        Returns:

        """
        self.Ckb_cli.version()

        # 1. generate account and build normal tx
        account = self.Ckb_cli.util_key_info_by_private_key(
            self.Config.ACCOUNT_PRIVATE_1
        )
        father_tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(
            self.Config.ACCOUNT_PRIVATE_1,
            account["address"]["testnet"],
            100000,
            self.node.getClient().url,
            "1500000",
        )

        tx = self.Tx.build_send_transfer_self_tx_with_input(
            [father_tx_hash],
            ["0x0"],
            self.Config.ACCOUNT_PRIVATE_1,
            output_count=15,
            fee=15000,
            api_url=self.node.getClient().url,
        )
        # 2. send the normal tx
        tx_hash = self.node.getClient().send_transaction(tx)

        tx_info = self.Ckb_cli.get_transaction(
            tx_hash, api_url=self.node.getClient().url
        )

        print("\n=========== Transaction Information ===========")
        print("Fee:                ", tx_info.get("fee"))
        print("Min Replace Fee:    ", tx_info.get("min_replace_fee"))
        print("Time Added to Pool: ", tx_info.get("time_added_to_pool"))
        print("===============================================\n")

        rpc_tx_info = self.node.getClient().get_transaction(tx_hash)
        fee_int = int(rpc_tx_info.get("fee", "0x0"), 16)
        min_replace_fee_int = int(rpc_tx_info.get("min_replace_fee", "0x0"), 16)

        fee = f"{fee_int / 100_000_000:.8f}".rstrip("0").rstrip(".")
        min_replace_fee = f"{min_replace_fee_int / 100_000_000:.8f}".rstrip("0").rstrip(
            "."
        )
        time_added_to_pool = int(rpc_tx_info.get("time_added_to_pool", "0x0"), 16)

        assert tx_info.get("fee") == fee
        assert tx_info.get("min_replace_fee") == min_replace_fee
        assert tx_info.get("time_added_to_pool") == time_added_to_pool

        self.Miner.miner_until_tx_committed(self.node, tx_hash, 1000)

    def test_02_tx_add_input_skip_check(self):
        tmp_tx_file = "/tmp/skip_check.json"
        api_url = "https://testnet.ckbapp.dev"
        # joyid lock script
        # https://testnet.explorer.nervos.org/transaction/0x1343ff1daaccd170947b72aa54da121a67a2b06916b9e7caddb882eb878d1152
        tx_hash = "0x1343ff1daaccd170947b72aa54da121a67a2b06916b9e7caddb882eb878d1152"
        self.Ckb_cli.tx_init(tmp_tx_file, api_url)
        self.Ckb_cli.tx_add_input(tx_hash, 0, tmp_tx_file, api_url)

        with open(tmp_tx_file, "r") as f:
            data = json.load(f)

        inputs = data.get("transaction", {}).get("inputs", [])
        if inputs:
            previous_output = inputs[0].get("previous_output", {})
            print("previous_output.tx_hash:", previous_output.get("tx_hash"))
            print("previous_output.index:", previous_output.get("index"))
            assert previous_output.get("tx_hash") == tx_hash
            assert previous_output.get("index") == "0x0"
        else:
            assert False, "No inputs found in the tx_file."
