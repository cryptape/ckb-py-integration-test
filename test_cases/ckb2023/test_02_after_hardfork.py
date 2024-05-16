import pytest

from framework.basic import CkbTest


class TestAfterHardFork(CkbTest):
    cluster:CkbTest.Cluster

    @classmethod
    def setup_class(cls):
        """
        1. star 4 node in tmp/cluster/hardFork dir
        2. link ckb node each other
        3. deploy contract
        4. miner 1000 block
        Returns:

        """

        # 1. star 4 node in tmp/cluster/hardFork dir
        nodes = [
            cls.CkbNode.init_dev_by_port(cls.CkbNodeConfigPath.CURRENT_TEST, "cluster/hardFork/node{i}".format(i=i),
                                         8114 + i,
                                         8225 + i)
            for
            i in range(1, 5)
        ]
        cls.cluster = cls.Cluster(nodes)
        cls.cluster.prepare_all_nodes()
        cls.cluster.start_all_nodes()

        # 2. link ckb node each other
        cls.cluster.connected_all_nodes()

        # 3. deploy contract
        contracts = cls.Contract_util.deploy_contracts(cls.Config.ACCOUNT_PRIVATE_1, cls.cluster.ckb_nodes[0])
        cls.spawn_contract = contracts["SpawnContract"]

        # 4. miner 1000 block
        cls.Miner.make_tip_height_number(cls.cluster.ckb_nodes[0], 1000)
        cls.Node.wait_cluster_height(cls.cluster, 1000, 100)

    @classmethod
    def teardown_class(cls):
        print("\nTeardown TestClass1")
        cls.cluster.stop_all_nodes()
        cls.cluster.clean_all_nodes()

    def setup_method(self, method):
        super().setup_method(method)
        current_epoch_result = self.cluster.ckb_nodes[0].getClient().get_current_epoch()
        consensus_response = self.cluster.ckb_nodes[0].getClient().get_consensus()
        # current epoch <  consensus epoch .length
        assert int(current_epoch_result['number'].replace("0x", "")) >= get_epoch_number_by_consensus_response(
            consensus_response, '0048')

    def test_01_0048_block_version_0x(self):
        """
        After the fork, the miner's block version is 0x0.
        1. miner version:0x0
        - block mining successful.
        :return:
        """

        # 1. miner version:0x0
        before_miner_num = self.cluster.ckb_nodes[0].getClient().get_tip_block_number()
        self.Miner.miner_with_version(self.cluster.ckb_nodes[0], "0x0")
        after_miner_num = self.cluster.ckb_nodes[0].getClient().get_tip_block_number()
        assert after_miner_num > before_miner_num

    def test_02_0048_block_version_0x1(self):
        """
        After the fork, the miner's block version is 0x1.
        1. miner version:0x1
        - block mining successful.
       :return:
        """

        # 1. miner version:0x1
        before_miner_num = self.cluster.ckb_nodes[0].getClient().get_tip_block_number()
        self.Miner.miner_with_version(self.cluster.ckb_nodes[0], "0x1")
        after_miner_num = self.cluster.ckb_nodes[0].getClient().get_tip_block_number()
        assert after_miner_num > before_miner_num

    def test_03_0048_block_version_0xffffff(self):
        """
            After the fork, the miner's block version is 0xffffff.
            # 1. miner version:0xffffff
            - block mining successful.
           :return:
        """

        # # 1. miner version:0xffffff
        before_miner_num = self.cluster.ckb_nodes[0].getClient().get_tip_block_number()
        self.Miner.miner_with_version(self.cluster.ckb_nodes[0], "0xffffffff")
        after_miner_num = self.cluster.ckb_nodes[0].getClient().get_tip_block_number()
        assert after_miner_num > before_miner_num

    def test_04_0048_block_version_0x100000000(self):
        """
            After the fork, the miner's block version is 0x100000000, return error
            1. miner version: 0x100000000
           - error : number too large to fit
           :return:
        """

        # 1. miner version: 0x100000000
        with pytest.raises(Exception) as exc_info:
            self.Miner.miner_with_version(self.cluster.ckb_nodes[0], "0x100000000")
        expected_error_message = "number too large to fit"
        assert expected_error_message in exc_info.value.args[0], \
            f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

    def test_05_send_tx_when_after_0th_fork(self):
        """
            The first block sends a regular transaction.
            - return tx_hash
            - The transaction status is queried as unknown for the first ten blocks.
            - The transaction will be committed on the blockchain after ten blocks.
            :return:

            1. make tip block is 0th for fork
            2. send tx
            3. query tx status is unknown
            4. miner 30 block
            5. query statue is committed and commit  block > 1010
        """

        # 1. make tip block is 0th for fork
        for node in self.cluster.ckb_nodes:
            self.Miner.make_tip_height_number(node, 1000)
        account = self.Ckb_cli.util_key_info_by_private_key(account_private=self.Config.ACCOUNT_PRIVATE_2)

        # 2. send tx
        tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(self.Config.ACCOUNT_PRIVATE_1,
                                                              account["address"]["testnet"],
                                                              140,
                                                              self.cluster.ckb_nodes[0].client.url)
        # 3. query tx status is unknown
        self.Miner.miner_with_version(self.cluster.ckb_nodes[0], '0x0')
        tx_response = self.cluster.ckb_nodes[0].getClient().get_transaction(tx_hash)
        print(f"tx response:{tx_response['tx_status']['status']}")
        assert tx_response['tx_status']['status'] == 'unknown'

        # 4. miner 30 block
        for i in range(30):
            self.Miner.miner_with_version(self.cluster.ckb_nodes[0], '0x0')
        tx_response = self.cluster.ckb_nodes[0].getClient().get_transaction(tx_hash)

        # 5. query statue is committed and commit  block > 1010
        print(f"tx response:{tx_response['tx_status']['status']}")
        block = self.cluster.ckb_nodes[0].getClient().get_block(tx_response['tx_status']['block_hash'])
        print(int(block["header"]["number"], 16))
        assert int(block["header"]["number"], 16) >= 1010

    def test_06_0049_send_data2_tx(self):
        """
        After a period of hard fork, a data2 transaction is sent.
        - return tx_hash
        - The transaction will be committed on the blockchain
        :return:
        # 1. miner 10 block
        # 2. send tx contains data2
        # 3. miner until tx committed
        """

        # 1. miner 10 block
        for i in range(10):
            self.Miner.miner_with_version(self.cluster.ckb_nodes[0], "0x0")

        # 2. send tx contains data2
        # send account 1 transfer data2
        # @ckb-lumos/helpers.encodeToAddress(
        #     {
        #         hashType:"data2",
        #         args:"0x",
        #         codeHash:"0x69c80d6a8104994bddc132bb568c953d60fae0ac928ad887c96de8434ca2a790"
        #     }
        # )
        # ckt1qp5usrt2syzfjj7acyetk45vj57kp7hq4jfg4ky8e9k7ss6v52neqpqh7xtq0
        tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(self.Config.MINER_PRIVATE_1,
                                                              "ckt1qp5usrt2syzfjj7acyetk45vj57kp7hq4jfg4ky8e9k7ss6v52neqpqh7xtq0",
                                                              140,
                                                              self.cluster.ckb_nodes[0].client.url)

        # 3. miner until tx committed
        self.Miner.miner_with_version(self.cluster.ckb_nodes[0], "0x0")
        self.Miner.miner_until_tx_committed(self.cluster.ckb_nodes[0], tx_hash)
        tx_response = self.cluster.ckb_nodes[0].getClient().get_transaction(tx_hash)
        print(f"tx response:{tx_response['tx_status']['status']}")
        assert tx_response['tx_status']['status'] == "committed"

    def test_07_0050_spawn_use_data2(self):
        """
            After a period of hard fork,send spawn tx by data2 .
            - return tx_hash
            - The transaction will be committed on the blockchain
            1. miner 11 block
            2. send tx contains spawn opcode
            3. miner until tx committed
        :return:
        """

        # 1. miner 11 block
        for _ in range(11):
            self.Miner.miner_with_version(self.cluster.ckb_nodes[0], "0x0")

        # 2. send tx contains spawn opcode
        code_tx_hash, code_tx_index = self.spawn_contract.get_deploy_hash_and_index()
        invoke_arg, invoke_data = self.spawn_contract.get_arg_and_data("demo")
        tx_hash = self.Contract.invoke_ckb_contract(self.Config.MINER_PRIVATE_1, code_tx_hash, code_tx_index,
                                                    invoke_arg, "data2", invoke_data,
                                                    api_url=self.cluster.ckb_nodes[0].getClient().url)

        # 3. miner until tx committed
        self.Miner.miner_until_tx_committed(self.cluster.ckb_nodes[0], tx_hash)

    def test_08_0050_spawn_use_data1(self):
        """
        After a period of hard fork,send spawn tx by data1 .
            - return Error: InvalidEcall(2101)

        1. send tx contains spawn opcode use data1
            - return Error: InvalidEcall(2101)
        :return:
        """

        #  1. send tx contains spawn opcode use data1
        code_tx_hash, code_tx_index = self.spawn_contract.get_deploy_hash_and_index()
        invoke_arg, invoke_data = self.spawn_contract.get_arg_and_data("demo")
        with pytest.raises(Exception) as exc_info:
            self.Contract.invoke_ckb_contract(self.Config.MINER_PRIVATE_1, code_tx_hash, code_tx_index,
                                                        invoke_arg, "data1",
                                                        invoke_data,
                                                        api_url=self.cluster.ckb_nodes[0].getClient().url)
        expected_error_message = "InvalidEcall(2101)"
        assert expected_error_message in exc_info.value.args[0], \
            f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

    def test_09_0050_spawn_use_data(self):
        """
          After a period of hard fork,send spawn tx by data1 .
            - return Error: InvalidInstruction

        1. send tx contains spawn opcode use data
            - return Error: InvalidEcall(2101)
        :return:
        """

        # 1. send tx contains spawn opcode use data
        code_tx_hash, code_tx_index = self.spawn_contract.get_deploy_hash_and_index()
        invoke_arg, invoke_data = self.spawn_contract.get_arg_and_data("demo")
        with pytest.raises(Exception) as exc_info:
            self.Contract.invoke_ckb_contract(self.Config.MINER_PRIVATE_1, code_tx_hash, code_tx_index,
                                                        invoke_arg, "data", invoke_data,
                                                        api_url=self.cluster.ckb_nodes[0].getClient().url)
        expected_error_message = "InvalidInstruction"
        assert expected_error_message in exc_info.value.args[0], \
            f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

    def test_10_0050_spawn_use_type(self):
        """
        After a period of hard fork,send spawn tx by data1 .
        - return tx_hash
        - The transaction will be committed on the blockchain

        1. miner 11 block
        2. send tx contains spawn opcode use type
        3. miner until tx committed
        :return:
        """

        # 1. miner 11 block
        for i in range(11):
            self.Miner.miner_with_version(self.cluster.ckb_nodes[0], "0x0")

        # 2. send tx contains spawn opcode use type
        code_tx_hash, code_tx_index = self.spawn_contract.get_deploy_hash_and_index()
        invoke_arg, invoke_data = self.spawn_contract.get_arg_and_data("demo")
        tx_hash = self.Contract.invoke_ckb_contract(self.Config.MINER_PRIVATE_1, code_tx_hash, code_tx_index,
                                                    invoke_arg, "type", invoke_data,
                                                    api_url=self.cluster.ckb_nodes[0].getClient().url)

        # 3. miner until tx committed
        self.Miner.miner_until_tx_committed(self.cluster.ckb_nodes[0], tx_hash)


def get_epoch_number_by_consensus_response(consensus_response, rfc_name):
    return int(list(filter(lambda obj: rfc_name in obj['rfc'], consensus_response['hardfork_features']))[0][
                   'epoch_number'].replace("0x", ""), 16)
