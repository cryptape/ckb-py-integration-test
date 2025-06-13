import pytest

from framework.basic import CkbTest
from framework.helper.ckb_cli import (
    tx_build_multisig_address,
    tx_init,
    tx_add_multisig_config_for_addr_list,
    tx_add_input,
    tx_add_output_multisig,
    tx_info,
    tx_sign_inputs,
    tx_add_signature,
    tx_send,
    wallet_get_capacity,
)
from framework.util import decodeAddress


class TestCkbCliMultisig202(CkbTest):

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

    def test_01_build_multisig_address(self):
        """
        1. build multisig address by old contract (legacy、old multisig code hash)
        2. build multisig address by new contract (v2、new multisig code hash)
        3. check addresses code hash

        address, private key
        ckt1qzda0cr08m85hc8jlnfp3zer7xulejywt49kt2rr0vthywaa50xwsqvad384xh4xnrk6ljgrlqrgmvwvh06edxqzdtepp, 0xfd134cb90f7967241612648ed5e4a7aea712ed96492e884d43979a902b39dd3c
        ckt1qzda0cr08m85hc8jlnfp3zer7xulejywt49kt2rr0vthywaa50xwsqt6p0y7f9ax3lssgt645z3e4lgem24myuguaqxnl, 0x0d5523df2a0e0bf8364069ecd2f7c68c8866838a2d5ab8e773a4fe488435b8c4
        ckt1qzda0cr08m85hc8jlnfp3zer7xulejywt49kt2rr0vthywaa50xwsqt79hml345tahkt0682ayphvfhjw3pklsgtj3n9c, 0xbb2b1757c804819c6bbabf30b5a839125b0ea29420fb5fe0edbeac447ca38947
        ckt1qzda0cr08m85hc8jlnfp3zer7xulejywt49kt2rr0vthywaa50xwsqtsk4updd44n8cnez0m7flny2s85a23slgf03pag, 0xc47df09701edeb9b2da29edae1a2c698623683f1bbc8cdc197c391bd08d92a90
        ckt1qzda0cr08m85hc8jlnfp3zer7xulejywt49kt2rr0vthywaa50xwsqtvqkxczfqxug0at9hfw74kua540l94sccvqppyt, 0xe3c331a6366fa12618e11472a502c0d65bf2c3e66100c84db316ea0258e1b40e
        ckt1qzda0cr08m85hc8jlnfp3zer7xulejywt49kt2rr0vthywaa50xwsq2x8ejhvjzep8ehmqqx85v8hw0se942snsldfhe7, 0xcc3e78f7c58cd32c8298864aeaa5a7fdd7a4e547590ec4b0d0be7f661c58b7a6
        ckt1qzda0cr08m85hc8jlnfp3zer7xulejywt49kt2rr0vthywaa50xwsqdga63vgayk7y8l837gy99ae0y6mfh676s2n4zmp, 0x9707bf0855e205a5b67a2f60f2bcaac285afe5d84f31262c362658f3a947c437
        ckt1qzda0cr08m85hc8jlnfp3zer7xulejywt49kt2rr0vthywaa50xwsqd2sm262k3l0pm22l6mnhstrplg85m8caqqk53kv, 0x02127e7a294269ca8ecaf97aa33a4e89d8a1553de0a0c031e0e9fb0939dff03e
        ckt1qzda0cr08m85hc8jlnfp3zer7xulejywt49kt2rr0vthywaa50xwsqvge8xqhac3hw7jtnz6q2vz0exw8yek2kc84nqzp, 0x6f358b8cda4707021f4655aeb792cdfeef5c24a019faf77faae8fb859dbe2e47
        ckt1qzda0cr08m85hc8jlnfp3zer7xulejywt49kt2rr0vthywaa50xwsqt26vvgpxsacml8770tn6lne8yynjw7q9s9up5a2, 0x28724779a6baff60beab19884fdf50bc22887dbe5d005b457e89691bf9054bad
        """
        addresses = [
            "ckt1qzda0cr08m85hc8jlnfp3zer7xulejywt49kt2rr0vthywaa50xwsqvad384xh4xnrk6ljgrlqrgmvwvh06edxqzdtepp",
            "ckt1qzda0cr08m85hc8jlnfp3zer7xulejywt49kt2rr0vthywaa50xwsqt6p0y7f9ax3lssgt645z3e4lgem24myuguaqxnl",
            "ckt1qzda0cr08m85hc8jlnfp3zer7xulejywt49kt2rr0vthywaa50xwsqt79hml345tahkt0682ayphvfhjw3pklsgtj3n9c",
        ]

        self.Ckb_cli.version()

        # old
        output_legacy = tx_build_multisig_address(
            addresses,
            threshold=len(addresses),
            multisig_code_hash="legacy",
            api_url=self.node.getClient().url,
        )
        output_by_old_code_hash = tx_build_multisig_address(
            addresses,
            threshold=len(addresses),
            multisig_code_hash="0x5c5069eb0857efc65e1bca0c07df34c31663b3622fd3876c876320fc9634e2a8",
            api_url=self.node.getClient().url,
        )
        assert output_legacy == output_by_old_code_hash

        # old testnet multisig address
        legacy_testnet_address = output_legacy["testnet"]
        assert (
            legacy_testnet_address
            == "ckt1qpw9q60tppt7l3j7r09qcp7lxnp3vcanvgha8pmvsa3jplykxn32sqgd9lx3ncep73qcfl498e3rge9uel6wyzsf4jqxf"
        )
        legacy_testnet_decode = decodeAddress(legacy_testnet_address, "testnet")
        assert (
            legacy_testnet_decode[1]
            == "0x5c5069eb0857efc65e1bca0c07df34c31663b3622fd3876c876320fc9634e2a8"
        )
        # old mainnet multisig address
        legacy_mainnet_address = output_legacy["mainnet"]
        assert (
            legacy_mainnet_address
            == "ckb1qpw9q60tppt7l3j7r09qcp7lxnp3vcanvgha8pmvsa3jplykxn32sqgd9lx3ncep73qcfl498e3rge9uel6wyzs88e0v3"
        )
        legacy_mainnet_decode = decodeAddress(legacy_mainnet_address, "mainnet")
        assert (
            legacy_mainnet_decode[1]
            == "0x5c5069eb0857efc65e1bca0c07df34c31663b3622fd3876c876320fc9634e2a8"
        )

        # new
        output_v2 = tx_build_multisig_address(
            addresses,
            threshold=len(addresses),
            multisig_code_hash="v2",
            api_url=self.node.getClient().url,
        )
        output_by_new_code_hash = tx_build_multisig_address(
            addresses,
            threshold=len(addresses),
            multisig_code_hash="0x36c971b8d41fbd94aabca77dc75e826729ac98447b46f91e00796155dddb0d29",
            api_url=self.node.getClient().url,
        )
        assert output_v2 == output_by_new_code_hash

        # new testnet multisig address
        v2_testnet_address = output_v2["testnet"]
        assert (
            v2_testnet_address
            == "ckt1qqmvjudc6s0mm992hjnhm367sfnjntycg3a5d7g7qpukz4wamvxjjqsd9lx3ncep73qcfl498e3rge9uel6wyzs9e9882"
        )
        v2_testnet_decode = decodeAddress(v2_testnet_address, "testnet")
        assert (
            v2_testnet_decode[1]
            == "0x36c971b8d41fbd94aabca77dc75e826729ac98447b46f91e00796155dddb0d29"
        )
        # new mainnet multisig address
        v2_mainnet_address = output_v2["mainnet"]
        assert (
            v2_mainnet_address
            == "ckb1qqmvjudc6s0mm992hjnhm367sfnjntycg3a5d7g7qpukz4wamvxjjqsd9lx3ncep73qcfl498e3rge9uel6wyzsttwgdj"
        )
        v2_mainnet_decode = decodeAddress(v2_mainnet_address, "mainnet")
        assert (
            v2_mainnet_decode[1]
            == "0x36c971b8d41fbd94aabca77dc75e826729ac98447b46f91e00796155dddb0d29"
        )

    def test_02_multisig_tx_legacy(self):
        """
        1.	Recharge the multisig address
            2.	Construct multisig.json (transfer from the multisig address to yourself and a regular address)
            3.	Each of the three addresses corresponding to the multisig signs the transaction
            4.	Send the transaction
            5.	Check the balance of the multisig address to verify whether the transfer was successful
        Returns:
        """
        tmp_tx_file = "/tmp/multisig.json"

        tx_init(tmp_tx_file, self.node.getClient().url)

        addresses = [
            "ckt1qzda0cr08m85hc8jlnfp3zer7xulejywt49kt2rr0vthywaa50xwsqvad384xh4xnrk6ljgrlqrgmvwvh06edxqzdtepp",
            "ckt1qzda0cr08m85hc8jlnfp3zer7xulejywt49kt2rr0vthywaa50xwsqt6p0y7f9ax3lssgt645z3e4lgem24myuguaqxnl",
            "ckt1qzda0cr08m85hc8jlnfp3zer7xulejywt49kt2rr0vthywaa50xwsqt79hml345tahkt0682ayphvfhjw3pklsgtj3n9c",
        ]
        # add_multisig_config
        tx_add_multisig_config_for_addr_list(
            addresses,
            tmp_tx_file,
            threshold=len(addresses),
            multisig_code_hash="legacy",
            api_url=self.node.getClient().url,
        )

        multisig_addr = "ckt1qpw9q60tppt7l3j7r09qcp7lxnp3vcanvgha8pmvsa3jplykxn32sqgd9lx3ncep73qcfl498e3rge9uel6wyzsf4jqxf"
        prepare_tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(
            self.Config.ACCOUNT_PRIVATE_1,
            multisig_addr,
            200,
            self.node.getClient().url,
            "1000",
        )
        self.Miner.miner_until_tx_committed(self.node, prepare_tx_hash, 1000)

        tx_add_input(prepare_tx_hash, 0, tmp_tx_file, self.node.getClient().url)

        tx_add_output_multisig(
            address=multisig_addr,
            capacity=119.99,
            tx_file=tmp_tx_file,
            is_multisig=True,
            api_url=self.node.getClient().url,
        )
        tx_add_output_multisig(
            address="ckt1qzda0cr08m85hc8jlnfp3zer7xulejywt49kt2rr0vthywaa50xwsqt26vvgpxsacml8770tn6lne8yynjw7q9s9up5a2",
            capacity=80,
            tx_file=tmp_tx_file,
            is_multisig=False,
            api_url=self.node.getClient().url,
        )

        tx_info(tmp_tx_file, self.node.getClient().url)

        private_key1 = (
            "0xfd134cb90f7967241612648ed5e4a7aea712ed96492e884d43979a902b39dd3c"
        )
        private_key2 = (
            "0x0d5523df2a0e0bf8364069ecd2f7c68c8866838a2d5ab8e773a4fe488435b8c4"
        )
        private_key3 = (
            "0xbb2b1757c804819c6bbabf30b5a839125b0ea29420fb5fe0edbeac447ca38947"
        )
        sign_data1 = tx_sign_inputs(
            private_key1, tmp_tx_file, self.node.getClient().url
        )
        sign_data2 = tx_sign_inputs(
            private_key2, tmp_tx_file, self.node.getClient().url
        )
        sign_data3 = tx_sign_inputs(
            private_key3, tmp_tx_file, self.node.getClient().url
        )

        tx_add_signature(
            sign_data1[0]["lock-arg"],
            sign_data1[0]["signature"],
            tmp_tx_file,
            self.node.getClient().url,
        )
        tx_add_signature(
            sign_data2[0]["lock-arg"],
            sign_data2[0]["signature"],
            tmp_tx_file,
            self.node.getClient().url,
        )
        tx_add_signature(
            sign_data3[0]["lock-arg"],
            sign_data3[0]["signature"],
            tmp_tx_file,
            self.node.getClient().url,
        )

        tx_hash = tx_send(tmp_tx_file, self.node.getClient().url).strip()
        self.Miner.miner_until_tx_committed(self.node, tx_hash, 1000)

        balance = wallet_get_capacity(multisig_addr, self.node.getClient().url)
        assert balance == 119.99

    @pytest.mark.skip
    def test_03_multisig_tx_v2(self):
        """
        Wait until https://github.com/nervosnetwork/ckb/pull/4872 is merged, then skip no longer.
        Returns:

        """
        tmp_tx_file = "/tmp/multisig_v2.json"

        tx_init(tmp_tx_file, self.node.getClient().url)

        addresses = [
            "ckt1qzda0cr08m85hc8jlnfp3zer7xulejywt49kt2rr0vthywaa50xwsqvad384xh4xnrk6ljgrlqrgmvwvh06edxqzdtepp",
            "ckt1qzda0cr08m85hc8jlnfp3zer7xulejywt49kt2rr0vthywaa50xwsqt6p0y7f9ax3lssgt645z3e4lgem24myuguaqxnl",
            "ckt1qzda0cr08m85hc8jlnfp3zer7xulejywt49kt2rr0vthywaa50xwsqt79hml345tahkt0682ayphvfhjw3pklsgtj3n9c",
        ]
        # add_multisig_config
        tx_add_multisig_config_for_addr_list(
            addresses,
            tmp_tx_file,
            threshold=len(addresses),
            multisig_code_hash="v2",
            api_url=self.node.getClient().url,
        )

        multisig_addr = "ckt1qqmvjudc6s0mm992hjnhm367sfnjntycg3a5d7g7qpukz4wamvxjjqsd9lx3ncep73qcfl498e3rge9uel6wyzs9e9882"
        prepare_tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(
            self.Config.ACCOUNT_PRIVATE_1,
            multisig_addr,
            200,
            self.node.getClient().url,
            "1000",
        )
        self.Miner.miner_until_tx_committed(self.node, prepare_tx_hash, 1000)

        tx_add_input(prepare_tx_hash, 0, tmp_tx_file, self.node.getClient().url)

        tx_add_output_multisig(
            address=multisig_addr,
            capacity=119.99,
            tx_file=tmp_tx_file,
            is_multisig=True,
            api_url=self.node.getClient().url,
        )
        tx_add_output_multisig(
            address="ckt1qzda0cr08m85hc8jlnfp3zer7xulejywt49kt2rr0vthywaa50xwsqt26vvgpxsacml8770tn6lne8yynjw7q9s9up5a2",
            capacity=80,
            tx_file=tmp_tx_file,
            is_multisig=False,
            api_url=self.node.getClient().url,
        )

        tx_info(tmp_tx_file, self.node.getClient().url)

        private_key1 = (
            "0xfd134cb90f7967241612648ed5e4a7aea712ed96492e884d43979a902b39dd3c"
        )
        private_key2 = (
            "0x0d5523df2a0e0bf8364069ecd2f7c68c8866838a2d5ab8e773a4fe488435b8c4"
        )
        private_key3 = (
            "0xbb2b1757c804819c6bbabf30b5a839125b0ea29420fb5fe0edbeac447ca38947"
        )
        sign_data1 = tx_sign_inputs(
            private_key1, tmp_tx_file, self.node.getClient().url
        )
        sign_data2 = tx_sign_inputs(
            private_key2, tmp_tx_file, self.node.getClient().url
        )
        sign_data3 = tx_sign_inputs(
            private_key3, tmp_tx_file, self.node.getClient().url
        )

        tx_add_signature(
            sign_data1[0]["lock-arg"],
            sign_data1[0]["signature"],
            tmp_tx_file,
            self.node.getClient().url,
        )
        tx_add_signature(
            sign_data2[0]["lock-arg"],
            sign_data2[0]["signature"],
            tmp_tx_file,
            self.node.getClient().url,
        )
        tx_add_signature(
            sign_data3[0]["lock-arg"],
            sign_data3[0]["signature"],
            tmp_tx_file,
            self.node.getClient().url,
        )

        tx_hash = tx_send(tmp_tx_file, self.node.getClient().url).strip()
        self.Miner.miner_until_tx_committed(self.node, tx_hash, 1000)

        balance = wallet_get_capacity(multisig_addr, self.node.getClient().url)
        assert balance == 119.99
