import time

import pytest

from framework.basic import CkbTest
from framework.helper.udt_contract import UdtContract, issue_udt_tx
from framework.test_fiber import Fiber, FiberConfigPath
from framework.util import generate_random_preimage
from test_cases.fiber.devnet.test_fiber import wait_for_channel_state


#
class OpenChannelTest(CkbTest):
    """
    test1 : 未连接的peer_id

    """

    @classmethod
    def setup_class(cls):
        cls.account1 = cls.Ckb_cli.util_key_info_by_private_key(
            cls.Config.ACCOUNT_PRIVATE_1
        )
        cls.account2 = cls.Ckb_cli.util_key_info_by_private_key(
            cls.Config.ACCOUNT_PRIVATE_2
        )
        cls.node = cls.CkbNode.init_dev_by_port(
            cls.CkbNodeConfigPath.CURRENT_FIBER, "contract/node", 8114, 8115
        )

        cls.node.prepare()
        cls.node.start()
        cls.node.getClient().get_consensus()
        cls.Miner.make_tip_height_number(cls.node, 20)

    def setup_method(cls, method):
        cls.did_pass = None
        cls.fibers = []
        cls.fiber1 = Fiber.init_by_port(
            FiberConfigPath.V100_DEV,
            cls.Config.ACCOUNT_PRIVATE_1,
            "fiber/node1",
            "8228",
            "8227",
        )
        cls.fiber2 = Fiber.init_by_port(
            FiberConfigPath.V100_DEV,
            cls.Config.ACCOUNT_PRIVATE_2,
            "fiber/node2",
            "8229",
            "8230",
        )
        cls.fibers.append(cls.fiber1)
        cls.fibers.append(cls.fiber2)
        # # deploy xudt
        xudt_contract_hash = cls.node.getClient().get_block_by_number("0x0")[
            "transactions"
        ][0]["hash"]
        #
        cls.udtContract = UdtContract(xudt_contract_hash, 10)
        #
        deploy_hash, deploy_index = cls.udtContract.get_deploy_hash_and_index()

        # # issue
        tx_hash = issue_udt_tx(
            cls.udtContract,
            cls.node.rpcUrl,
            cls.Config.ACCOUNT_PRIVATE_1,
            cls.Config.ACCOUNT_PRIVATE_1,
            1000 * 100000000,
        )
        cls.Miner.miner_until_tx_committed(cls.node, tx_hash)
        cls.node.start_miner()
        # deploy fiber
        # start 2 fiber with xudt

        cls.fiber1.prepare(
            update_config={
                "ckb_rpc_url": cls.node.rpcUrl,
                "ckb_udt_whitelist": True,
                "xudt_script_code_hash": cls.Contract.get_ckb_contract_codehash(
                    deploy_hash, deploy_index, True, cls.node.rpcUrl
                ),
                "xudt_cell_deps_tx_hash": deploy_hash,
                "xudt_cell_deps_index": deploy_index,
            }
        )
        cls.fiber1.start(cls.node)

        cls.fiber2.prepare(
            update_config={
                "ckb_rpc_url": cls.node.rpcUrl,
                "ckb_udt_whitelist": True,
                "xudt_script_code_hash": cls.Contract.get_ckb_contract_codehash(
                    deploy_hash, deploy_index, True, cls.node.rpcUrl
                ),
                "xudt_cell_deps_tx_hash": deploy_hash,
                "xudt_cell_deps_index": deploy_index,
            }
        )
        cls.fiber2.start(cls.node)
        before_balance1 = cls.Ckb_cli.wallet_get_capacity(
            cls.account1["address"]["testnet"]
        )
        print("before_balance1:", before_balance1)
        cls.fiber1.connect_peer(cls.fiber2)
        time.sleep(1)
        print("\nSetting up method", method.__name__)

    def teardown_method(self, method):
        super().teardown_method(method)

        for fiber in self.fibers:
            fiber.stop()
            fiber.clean()

    @classmethod
    def teardown_class(cls):
        cls.node.stop()
        cls.node.clean()

    # def test_unlink_peer(self):
    #     """
    #     1. open channel 未连接的peer id
    #         Returns: pubkey not found
    #     """
    #     with pytest.raises(Exception) as exc_info:
    #         ret = self.fiber1.get_client().open_channel(
    #             {
    #                 "peer_id": "QmQTR428wfY8s5wFTwU6ZaNBCJg1RwWbDFdP2r1WPNBQX1",
    #                 "funding_amount": hex(1000 * 100000000),
    #                 "public": True,
    #                 "funding_udt_type_script": {
    #                     "code_hash": self.udtContract.get_code_hash(True, self.node.rpcUrl),
    #                     "hash_type": "type",
    #                     "args": self.udtContract.get_owner_arg_by_lock_arg(self.account1["lock_arg"]),
    #                 },
    #                 # "tlc_fee_proportional_millionths": "0x4B0",
    #             }
    #         )
    #
    #     expected_error_message = (
    #         "pubkey not found"
    #     )
    #     assert expected_error_message in exc_info.value.args[0], (
    #         f"Expected substring '{expected_error_message}' "
    #         f"not found in actual string '{exc_info.value.args[0]}'"
    #     )

    # pass
    def test_linked_peer(self):
        """
        1. open channel 连接的peer id
        Returns:
        """
        self.fiber1.connect_peer(self.fiber2)
        time.sleep(5)
        temporary_channel_id = self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(200 * 100000000),
                "public": True,
                # "tlc_fee_proportional_millionths": "0x4B0",
            }
        )
        time.sleep(1)
        wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
        )
        time.sleep(5)
        # transfer
        self.fiber1.get_client().graph_channels()
        self.fiber1.get_client().graph_nodes()
        payment_preimage = generate_random_preimage()
        invoice_balance = 100 * 100000000
        invoice = self.fiber2.get_client().new_invoice(
            {
                "amount": hex(invoice_balance),
                "currency": "Fibb",
                "description": "test invoice generated by node2",
                "expiry": "0xe10",
                "final_cltv": "0x28",
                "payment_preimage": payment_preimage,
                "hash_algorithm": "sha256",
            }
        )
        before_channel = self.fiber1.get_client().list_channels({})

        self.fiber1.get_client().send_payment(
            {
                "invoice": invoice["invoice_address"],
            }
        )
        time.sleep(10)
        after_channel = self.fiber1.get_client().list_channels({})
        assert (
            int(before_channel["channels"][0]["local_balance"], 16)
            - int(after_channel["channels"][0]["local_balance"], 16)
            == invoice_balance
        )

        channels = self.fiber1.get_client().list_channels(
            {"peer_id": self.fiber2.get_peer_id()}
        )
        N1N2_CHANNEL_ID = channels["channels"][0]["channel_id"]
        self.fiber1.get_client().graph_channels()

        before_balance1 = self.Ckb_cli.wallet_get_capacity(
            self.account1["address"]["testnet"]
        )
        before_balance2 = self.Ckb_cli.wallet_get_capacity(
            self.account2["address"]["testnet"]
        )
        # shut down
        self.fiber1.get_client().shutdown_channel(
            {
                "channel_id": N1N2_CHANNEL_ID,
                "close_script": {
                    "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
                    "hash_type": "type",
                    "args": self.account1["lock_arg"],
                },
                "fee_rate": "0x3FC",
            }
        )
        # todo wait close tx commit
        time.sleep(20)
        after_balance1 = self.Ckb_cli.wallet_get_capacity(
            self.account1["address"]["testnet"]
        )
        after_balance2 = self.Ckb_cli.wallet_get_capacity(
            self.account2["address"]["testnet"]
        )
        print("before_balance1:", before_balance1)
        print("before_balance2:", before_balance2)
        print("after_balance1:", after_balance1)
        print("after_balance2:", after_balance2)
        assert after_balance2 - before_balance2 == 162

    # def test_funding_udt_type_script_is_empty(self):
    #     """
    #     1. funding_udt_type_script is none
    #         默认为 ckb
    #     Returns:
    #     """
    #     self.test_linked_peer()
    #     time.sleep(5)
    #     self.test_linked_peer()

    # def test_funding_udt_type_script_not_exist_in_node1(self):
    #     """
    #     1. udt script 不在自己节点
    #     Returns:
    #     """
    #
    # def test_funding_udt_type_script_not_exist_in_node2(self):
    #     """
    #         1. udt script 不在对方节点
    #         Returns:
    #     """

    # def test_funding_udt_type_script_is_white(self):
    #     """
    #     1. funding_udt_type_script 在节点上
    #     Returns:
    #     """
    #     # open chanel for fiber
    #     account = self.Ckb_cli.util_key_info_by_private_key(
    #         self.Config.ACCOUNT_PRIVATE_1
    #     )
    #     account2 = self.Ckb_cli.util_key_info_by_private_key(
    #         self.Config.ACCOUNT_PRIVATE_2
    #     )
    #     # connect  2 fiber
    #     self.fiber1.connect_peer(self.fiber2)
    #     # todo wait peer connet
    #     time.sleep(1)
    #     # open channel
    #     temporary_channel_id = self.fiber1.get_client().open_channel(
    #         {
    #             "peer_id": self.fiber2.get_peer_id(),
    #             "funding_amount": hex(1000 * 100000000),
    #             "public": True,
    #             "funding_udt_type_script": {
    #                 "code_hash": self.udtContract.get_code_hash(True, self.node.rpcUrl),
    #                 "hash_type": "type",
    #                 "args": self.udtContract.get_owner_arg_by_lock_arg(account["lock_arg"]),
    #             },
    #             # "tlc_fee_proportional_millionths": "0x4B0",
    #         }
    #     )
    #     time.sleep(1)
    #     wait_for_channel_state(
    #         self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
    #     )
    #     # transfer
    #     self.fiber1.get_client().graph_channels()
    #     self.fiber1.get_client().graph_nodes()
    #     payment_preimage = generate_random_preimage()
    #     invoice_balance = 100 * 100000000
    #     invoice = self.fiber2.get_client().new_invoice(
    #         {
    #             "amount": hex(invoice_balance),
    #             "currency": "Fibb",
    #             "description": "test invoice generated by node2",
    #             "expiry": "0xe10",
    #             "final_cltv": "0x28",
    #             "payment_preimage": payment_preimage,
    #             "hash_algorithm": "sha256",
    #             "udt_type_script": {
    #                 "code_hash": self.udtContract.get_code_hash(True, self.node.rpcUrl),
    #                 "hash_type": "type",
    #                 "args": self.udtContract.get_owner_arg_by_lock_arg(account["lock_arg"]),
    #             },
    #         }
    #     )
    #     before_channel = self.fiber1.get_client().list_channels({})
    #
    #     self.fiber1.get_client().send_payment(
    #         {
    #             "invoice": invoice["invoice_address"],
    #         }
    #     )
    #     time.sleep(10)
    #     after_channel = self.fiber1.get_client().list_channels({})
    #     assert (
    #             int(before_channel["channels"][0]["local_balance"], 16)
    #             - int(after_channel["channels"][0]["local_balance"], 16)
    #             == invoice_balance
    #     )
    #
    #     channels = self.fiber1.get_client().list_channels(
    #         {"peer_id": self.fiber2.get_peer_id()}
    #     )
    #     N1N2_CHANNEL_ID = channels["channels"][0]["channel_id"]
    #     self.fiber1.get_client().graph_channels()
    #
    #     before_account1 = self.udtContract.list_cell(
    #         self.node.getClient(), account["lock_arg"], account["lock_arg"]
    #     )
    #     before_account2 = self.udtContract.list_cell(
    #         self.node.getClient(), account["lock_arg"], account2["lock_arg"]
    #     )
    #     # shut down
    #     self.fiber1.get_client().shutdown_channel(
    #         {
    #             "channel_id": N1N2_CHANNEL_ID,
    #             "close_script": {
    #                 "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
    #                 "hash_type": "type",
    #                 "args": account["lock_arg"],
    #             },
    #             "fee_rate": "0x3FC",
    #         }
    #     )
    #     # todo wait close txx commit
    #     time.sleep(20)
    #
    #     after_account1 = self.udtContract.list_cell(
    #         self.node.getClient(), account["lock_arg"], account["lock_arg"]
    #     )
    #     after_account2 = self.udtContract.list_cell(
    #         self.node.getClient(), account["lock_arg"], account2["lock_arg"]
    #     )
    #
    #     print(before_account1)
    #     assert before_account1[0]["balance"] == 0
    #     print(before_account2)
    #     assert len(before_account2) == 0
    #     print(after_account1)
    #     assert after_account1[1]["balance"] == 90000000000
    #     print(after_account2)
    #     assert after_account2[0]["balance"] == 10000000000
    #     before_balance1 = self.Ckb_cli.wallet_get_live_cells(
    #         account["address"]["testnet"]
    #     )
    #     print("before_balance1:", before_balance1)

    # def test_funding_amount_ckb_is_zero(self):
    #     """
    #     1. funding_udt_type_script is None ,funding_amount = 0
    #     Returns:
    #     """
    #     with pytest.raises(Exception) as exc_info:
    #         temporary_channel_id = self.fiber1.get_client().open_channel(
    #             {
    #                 "peer_id": self.fiber2.get_peer_id(),
    #                 "funding_amount": hex(0),
    #                 "public": True,
    #                 # "tlc_fee_proportional_millionths": "0x4B0",
    #             }
    #         )
    #     expected_error_message = (
    #         "The funding amount should be greater than the reserved amount: 6200000000"
    #     )
    #     assert expected_error_message in exc_info.value.args[0], (
    #         f"Expected substring '{expected_error_message}' "
    #         f"not found in actual string '{exc_info.value.args[0]}'"
    #     )

    # def test_funding_amount_ckb_lt_62(self):
    #     """
    #     1. funding_udt_type_script is None ,funding_amount < 62
    #     Returns:
    #     """
    #     """
    #             1. funding_udt_type_script is None ,funding_amount = 0
    #             Returns:
    #             """
    #     with pytest.raises(Exception) as exc_info:
    #         temporary_channel_id = self.fiber1.get_client().open_channel(
    #             {
    #                 "peer_id": self.fiber2.get_peer_id(),
    #                 "funding_amount": hex(62 * 100000000 - 1),
    #                 "public": True,
    #                 # "tlc_fee_proportional_millionths": "0x4B0",
    #             }
    #         )
    #     expected_error_message = (
    #         "The funding amount should be greater than the reserve amount: 6200000000"
    #     )
    #     assert expected_error_message in exc_info.value.args[0], (
    #         f"Expected substring '{expected_error_message}' "
    #         f"not found in actual string '{exc_info.value.args[0]}'"
    #     )

    # def test_funding_amount_ckb_0xfffffffffffffffffffffffffffffff(self):
    #     """
    #             1. funding_udt_type_script is None ,funding_amount > account balance
    #             Returns:
    #             0xfffffffffffffffffffffffffffffff
    #             """
    #
    #     capacity = self.Ckb_cli.wallet_get_capacity(self.account2['address']['testnet'])
    #     with pytest.raises(Exception) as exc_info:
    #         temporary_channel_id = self.fiber1.get_client().open_channel(
    #             {
    #                 "peer_id": self.fiber2.get_peer_id(),
    #                 "funding_amount": "0xfffffffffffffffffffffffffffffff",
    #                 "public": True,
    #                 # "tlc_fee_proportional_millionths": "0x4B0",
    #             }
    #         )
    #     expected_error_message = (
    #         "The funding amount should be less than 18446744073709551615"
    #     )
    #     assert expected_error_message in exc_info.value.args[0], (
    #         f"Expected substring '{expected_error_message}' "
    #         f"not found in actual string '{exc_info.value.args[0]}'"
    #     )

    # def test_funding_amount_ckb_gt_account_balance(self):
    #     """
    #     1. funding_udt_type_script is None ,funding_amount > account balance
    #     Returns:
    #     todo: should failed
    #     """
    #
    #     capacity = self.Ckb_cli.wallet_get_capacity(self.account2['address']['testnet'])
    #     temporary_channel_id = self.fiber2.get_client().open_channel(
    #         {
    #             "peer_id": self.fiber1.get_peer_id(),
    #             "funding_amount": hex(int(capacity) * 100000000 * 2),
    #             "public": True,
    #             # "tlc_fee_proportional_millionths": "0x4B0",
    #         }
    #     )
    #     time.sleep(1)
    #     wait_for_channel_state(
    #         self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
    #     )
    #     self.fiber1.get_client().graph_channels()

    # def test_funding_amount_ckb_eq_account_balance(self):
    #     """
    #     1. funding_udt_type_script is None ,funding_amount == account balance
    #     Returns:
    #     """
    #     capacity = self.Ckb_cli.wallet_get_capacity(self.account2['address']['testnet'])
    #     temporary_channel_id = self.fiber2.get_client().open_channel(
    #         {
    #             "peer_id": self.fiber1.get_peer_id(),
    #             "funding_amount": hex(int(capacity) * 100000000),
    #             "public": True,
    #             # "tlc_fee_proportional_millionths": "0x4B0",
    #         }
    #     )
    #     time.sleep(1)
    #     wait_for_channel_state(
    #         self.fiber2.get_client(), self.fiber1.get_peer_id(), "CHANNEL_READY", 120
    #     )

    # def test_funding_amount_ckb_lt_account_balance(self):
    #     """
    #     1. funding_udt_type_script is None ,funding_amount < account balance
    #     Returns:
    #     """
    #     self.test_linked_peer()

    # def test_account_cell_data_not_empty(self):
    #     """
    #     if account cell.data != empty
    #     Returns:
    #     """

    # def test_account_cell_gt_funding_amount_10ckb(self):
    #     """
    #     cell - funding_amount = 10 ckb
    #     Returns:
    #         open channel FAILED
    #     """
    #     capacity = self.Ckb_cli.wallet_get_capacity(self.account2['address']['testnet'])
    #     temporary_channel_id = self.fiber2.get_client().open_channel(
    #         {
    #             "peer_id": self.fiber1.get_peer_id(),
    #             "funding_amount": hex((int(capacity) - 10) * 100000000),
    #             "public": True,
    #             # "tlc_fee_proportional_millionths": "0x4B0",
    #         }
    #     )
    #     time.sleep(1)
    #     wait_for_channel_state(
    #         self.fiber2.get_client(), self.fiber1.get_peer_id(), "NEGOTIATING_FUNDING", 120
    #     )

    # def test_account_mutil_cell_gt_funding_amount(self):
    #     """
    #      N cell balance > funding_amount
    #     Returns:
    #     """
    #     account3_private_key = "0x100c06bfd800d27397002dca6fb0993d5ba6399b4238b2f29ee9deb97593d2b1"
    #     account3 = self.Ckb_cli.util_key_info_by_private_key(account3_private_key)
    #     tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(self.Config.ACCOUNT_PRIVATE_1,
    #                                                           account3["address"]["testnet"],
    #                                                           1000,
    #                                                           self.node.rpcUrl)
    #     self.Miner.miner_until_tx_committed(self.node, tx_hash)
    #     tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(self.Config.ACCOUNT_PRIVATE_1,
    #                                                           account3["address"]["testnet"],
    #                                                           1000,
    #                                                           self.node.rpcUrl)
    #     self.Miner.miner_until_tx_committed(self.node, tx_hash)
    #
    #     # start fiber3
    #     self.fiber3 = Fiber.init_by_port(
    #         FiberConfigPath.V100_DEV,
    #         account3_private_key,
    #         "fiber/node3",
    #         "8231",
    #         "8232",
    #     )
    #     self.fibers.append(self.fiber3)
    #     self.fiber3.prepare(
    #         update_config={
    #             "ckb_rpc_url": self.node.rpcUrl,
    #         }
    #     )
    #     self.fiber3.start(self.node)
    #     self.fiber3.connect_peer(self.fiber2)
    #     time.sleep(3)
    #     self.fiber3.get_client().open_channel({
    #
    #         "peer_id": self.fiber2.get_peer_id(),
    #         "funding_amount": hex(990 * 100000000),
    #         "public": True,
    #         # "tlc_fee_proportional_millionths": "0x4B0",
    #
    #     })
    #     time.sleep(1)
    #     wait_for_channel_state(
    #         self.fiber3.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
    #     )
    #     channels = self.fiber3.get_client().graph_channels()
    #     assert len(channels['channels']) == 1
    #     assert channels['channels'][0]['capacity'] == hex(1052 * 100000000)

    # def test_funding_amount_gt_int_max(self):
    #     """
    #     funding_amount > int.max
    #     Args:
    #         self:
    #     Returns:
    #     """
    #
    #     #  The funding amount should be less than 18446744073709551615
    #     with pytest.raises(Exception) as exc_info:
    #         temporary_channel_id = self.fiber1.get_client().open_channel(
    #             {
    #                 "peer_id": self.fiber2.get_peer_id(),
    #                 "funding_amount": hex(18446744073709551616),
    #                 "public": True,
    #                 # "tlc_fee_proportional_millionths": "0x4B0",
    #             }
    #         )
    #     expected_error_message = (
    #         "The funding amount should be less than 18446744073709551615"
    #     )
    #     assert expected_error_message in exc_info.value.args[0], (
    #         f"Expected substring '{expected_error_message}' "
    #         f"not found in actual string '{exc_info.value.args[0]}'"
    #     )

    # def test_public_none(self):
    #     """
    #     https://github.com/nervosnetwork/fiber/issues/268
    #     public :None
    #     Returns:
    #     """
    #     self.fiber1.connect_peer(self.fiber2)
    #     time.sleep(5)
    #     temporary_channel_id = self.fiber1.get_client().open_channel(
    #         {
    #             "peer_id": self.fiber2.get_peer_id(),
    #             "funding_amount": hex(200 * 100000000),
    #             # "tlc_fee_proportional_millionths": "0x4B0",
    #         }
    #     )
    #     time.sleep(1)
    #     wait_for_channel_state(
    #         self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
    #     )
    #     time.sleep(5)
    #     # transfer
    #     self.fiber1.get_client().graph_channels()
    #     self.fiber1.get_client().graph_nodes()
    #     payment_preimage = generate_random_preimage()
    #     invoice_balance = 100 * 100000000
    #     invoice = self.fiber2.get_client().new_invoice(
    #         {
    #             "amount": hex(invoice_balance),
    #             "currency": "Fibb",
    #             "description": "test invoice generated by node2",
    #             "expiry": "0xe10",
    #             "final_cltv": "0x28",
    #             "payment_preimage": payment_preimage,
    #             "hash_algorithm": "sha256",
    #         }
    #     )
    #     before_channel = self.fiber1.get_client().list_channels({})
    #
    #     self.fiber1.get_client().send_payment(
    #         {
    #             "invoice": invoice["invoice_address"],
    #         }
    #     )
    #     time.sleep(10)
    #     after_channel = self.fiber1.get_client().list_channels({})
    #     assert (
    #             int(before_channel["channels"][0]["local_balance"], 16)
    #             - int(after_channel["channels"][0]["local_balance"], 16)
    #             == invoice_balance
    #     )
    #
    #     channels = self.fiber1.get_client().list_channels(
    #         {"peer_id": self.fiber2.get_peer_id()}
    #     )
    #     N1N2_CHANNEL_ID = channels["channels"][0]["channel_id"]
    #     self.fiber1.get_client().graph_channels()
    #
    #     before_balance1 = self.Ckb_cli.wallet_get_capacity(
    #         self.account1["address"]["testnet"]
    #     )
    #     before_balance2 = self.Ckb_cli.wallet_get_capacity(
    #         self.account2["address"]["testnet"]
    #     )
    #     # shut down
    #     self.fiber1.get_client().shutdown_channel(
    #         {
    #             "channel_id": N1N2_CHANNEL_ID,
    #             "close_script": {
    #                 "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
    #                 "hash_type": "type",
    #                 "args": self.account1["lock_arg"],
    #             },
    #             "fee_rate": "0x3FC",
    #         }
    #     )
    #     # todo wait close tx commit
    #     time.sleep(20)
    #     after_balance1 = self.Ckb_cli.wallet_get_capacity(self.account1["address"]["testnet"])
    #     after_balance2 = self.Ckb_cli.wallet_get_capacity(
    #         self.account2["address"]["testnet"]
    #     )
    #     print("before_balance1:", before_balance1)
    #     print("before_balance2:", before_balance2)
    #     print("after_balance1:", after_balance1)
    #     print("after_balance2:", after_balance2)
    #
    # def test_public_false(self):
    #     """
    #     public : false
    #     Returns:
    #
    #     """
    #     self.fiber1.connect_peer(self.fiber2)
    #     time.sleep(5)
    #     temporary_channel_id = self.fiber1.get_client().open_channel(
    #         {
    #             "peer_id": self.fiber2.get_peer_id(),
    #             "funding_amount": hex(200 * 100000000),
    #             "public": False
    #             # "tlc_fee_proportional_millionths": "0x4B0",
    #         }
    #     )
    #     time.sleep(1)
    #     wait_for_channel_state(
    #         self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
    #     )
    #     time.sleep(5)
    #     # transfer
    #     self.fiber1.get_client().graph_channels()
    #     self.fiber1.get_client().graph_nodes()
    #     payment_preimage = generate_random_preimage()
    #     invoice_balance = 100 * 100000000
    #     invoice = self.fiber2.get_client().new_invoice(
    #         {
    #             "amount": hex(invoice_balance),
    #             "currency": "Fibb",
    #             "description": "test invoice generated by node2",
    #             "expiry": "0xe10",
    #             "final_cltv": "0x28",
    #             "payment_preimage": payment_preimage,
    #             "hash_algorithm": "sha256",
    #         }
    #     )
    #     before_channel = self.fiber1.get_client().list_channels({})
    #
    #     self.fiber1.get_client().send_payment(
    #         {
    #             "invoice": invoice["invoice_address"],
    #         }
    #     )
    #     time.sleep(10)
    #     after_channel = self.fiber1.get_client().list_channels({})
    #     assert (
    #             int(before_channel["channels"][0]["local_balance"], 16)
    #             - int(after_channel["channels"][0]["local_balance"], 16)
    #             == invoice_balance
    #     )
    #
    #     channels = self.fiber1.get_client().list_channels(
    #         {"peer_id": self.fiber2.get_peer_id()}
    #     )
    #     N1N2_CHANNEL_ID = channels["channels"][0]["channel_id"]
    #     self.fiber1.get_client().graph_channels()
    #
    #     before_balance1 = self.Ckb_cli.wallet_get_capacity(
    #         self.account1["address"]["testnet"]
    #     )
    #     before_balance2 = self.Ckb_cli.wallet_get_capacity(
    #         self.account2["address"]["testnet"]
    #     )
    #     # shut down
    #     self.fiber1.get_client().shutdown_channel(
    #         {
    #             "channel_id": N1N2_CHANNEL_ID,
    #             "close_script": {
    #                 "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
    #                 "hash_type": "type",
    #                 "args": self.account1["lock_arg"],
    #             },
    #             "fee_rate": "0x3FC",
    #         }
    #     )
    #     # todo wait close tx commit
    #     time.sleep(20)
    #     after_balance1 = self.Ckb_cli.wallet_get_capacity(self.account1["address"]["testnet"])
    #     after_balance2 = self.Ckb_cli.wallet_get_capacity(
    #         self.account2["address"]["testnet"]
    #     )
    #     print("before_balance1:", before_balance1)
    #     print("before_balance2:", before_balance2)
    #     print("after_balance1:", after_balance1)
    #     print("after_balance2:", after_balance2)
    #     assert after_balance2 - before_balance2 == 162
    #
    # def test_public_true(self):
    #     """
    #     public is true
    #     Returns:
    #
    #     """
    #     self.fiber1.connect_peer(self.fiber2)
    #     time.sleep(5)
    #     temporary_channel_id = self.fiber1.get_client().open_channel(
    #         {
    #             "peer_id": self.fiber2.get_peer_id(),
    #             "funding_amount": hex(200 * 100000000),
    #             "public": True
    #             # "tlc_fee_proportional_millionths": "0x4B0",
    #         }
    #     )
    #     time.sleep(1)
    #     wait_for_channel_state(
    #         self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
    #     )
    #     time.sleep(5)
    #     # transfer
    #     self.fiber1.get_client().graph_channels()
    #     self.fiber1.get_client().graph_nodes()
    #     payment_preimage = generate_random_preimage()
    #     invoice_balance = 100 * 100000000
    #     invoice = self.fiber2.get_client().new_invoice(
    #         {
    #             "amount": hex(invoice_balance),
    #             "currency": "Fibb",
    #             "description": "test invoice generated by node2",
    #             "expiry": "0xe10",
    #             "final_cltv": "0x28",
    #             "payment_preimage": payment_preimage,
    #             "hash_algorithm": "sha256",
    #         }
    #     )
    #     before_channel = self.fiber1.get_client().list_channels({})
    #
    #     self.fiber1.get_client().send_payment(
    #         {
    #             "invoice": invoice["invoice_address"],
    #         }
    #     )
    #     time.sleep(10)
    #     after_channel = self.fiber1.get_client().list_channels({})
    #     assert (
    #             int(before_channel["channels"][0]["local_balance"], 16)
    #             - int(after_channel["channels"][0]["local_balance"], 16)
    #             == invoice_balance
    #     )
    #
    #     channels = self.fiber1.get_client().list_channels(
    #         {"peer_id": self.fiber2.get_peer_id()}
    #     )
    #     N1N2_CHANNEL_ID = channels["channels"][0]["channel_id"]
    #     self.fiber1.get_client().graph_channels()
    #
    #     before_balance1 = self.Ckb_cli.wallet_get_capacity(
    #         self.account1["address"]["testnet"]
    #     )
    #     before_balance2 = self.Ckb_cli.wallet_get_capacity(
    #         self.account2["address"]["testnet"]
    #     )
    #     # shut down
    #     self.fiber1.get_client().shutdown_channel(
    #         {
    #             "channel_id": N1N2_CHANNEL_ID,
    #             "close_script": {
    #                 "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
    #                 "hash_type": "type",
    #                 "args": self.account1["lock_arg"],
    #             },
    #             "fee_rate": "0x3FC",
    #         }
    #     )
    #     # todo wait close tx commit
    #     time.sleep(20)
    #     after_balance1 = self.Ckb_cli.wallet_get_capacity(self.account1["address"]["testnet"])
    #     after_balance2 = self.Ckb_cli.wallet_get_capacity(
    #         self.account2["address"]["testnet"]
    #     )
    #     print("before_balance1:", before_balance1)
    #     print("before_balance2:", before_balance2)
    #     print("after_balance1:", after_balance1)
    #     print("after_balance2:", after_balance2)
    #     assert after_balance2 - before_balance2 == 162

    # def test_shutdown_script_none(self):
    #     """
    #     shutdown_script:none
    #     Returns:
    #     """
    #     self.test_linked_peer()
    #
    # def test_shutdown_script_too_large(self):
    #     """
    #     Returns:
    #     """
    #     self.fiber1.connect_peer(self.fiber2)
    #     time.sleep(5)
    #     temporary_channel_id = self.fiber1.get_client().open_channel(
    #         {
    #             "peer_id": self.fiber2.get_peer_id(),
    #             "funding_amount": hex(200 * 100000000),
    #             "public": True,
    #             "shutdown_script": {
    #                 "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
    #                 "hash_type": "type",
    #                 "args": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9f9bd7e06f3ecf4be0f2fcd2188b23f1b9f9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce89bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce89bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce89bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce89bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce89bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce89bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce89bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce89bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce89bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce89bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce89bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce89bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce89bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce89bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce89bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce89bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce89bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
    #             }
    #             # "tlc_fee_proportional_millionths": "0x4B0",
    #
    #         }
    #     )
    #     time.sleep(1)
    #     wait_for_channel_state(
    #         self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
    #     )
    #     time.sleep(5)
    #     # transfer
    #     self.fiber1.get_client().graph_channels()
    #     self.fiber1.get_client().graph_nodes()
    #     payment_preimage = generate_random_preimage()
    #     invoice_balance = 100 * 100000000
    #     invoice = self.fiber2.get_client().new_invoice(
    #         {
    #             "amount": hex(invoice_balance),
    #             "currency": "Fibb",
    #             "description": "test invoice generated by node2",
    #             "expiry": "0xe10",
    #             "final_cltv": "0x28",
    #             "payment_preimage": payment_preimage,
    #             "hash_algorithm": "sha256",
    #         }
    #     )
    #     before_channel = self.fiber1.get_client().list_channels({})
    #
    #     self.fiber1.get_client().send_payment(
    #         {
    #             "invoice": invoice["invoice_address"],
    #         }
    #     )
    #     time.sleep(10)
    #     after_channel = self.fiber1.get_client().list_channels({})
    #     assert (
    #             int(before_channel["channels"][0]["local_balance"], 16)
    #             - int(after_channel["channels"][0]["local_balance"], 16)
    #             == invoice_balance
    #     )
    #
    #     channels = self.fiber1.get_client().list_channels(
    #         {"peer_id": self.fiber2.get_peer_id()}
    #     )
    #     N1N2_CHANNEL_ID = channels["channels"][0]["channel_id"]
    #     self.fiber1.get_client().graph_channels()
    #
    #     before_balance1 = self.Ckb_cli.wallet_get_capacity(
    #         self.account1["address"]["testnet"]
    #     )
    #     before_balance2 = self.Ckb_cli.wallet_get_capacity(
    #         self.account2["address"]["testnet"]
    #     )
    #     # shut down
    #     self.fiber2.get_client().shutdown_channel(
    #         {
    #             "channel_id": N1N2_CHANNEL_ID,
    #             "close_script": {
    #                 "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
    #                 "hash_type": "type",
    #                 "args": self.account2["lock_arg"],
    #             },
    #             "fee_rate": "0x3FC",
    #         }
    #     )
    #     # todo wait close tx commit
    #     time.sleep(20)
    #     after_balance1 = self.Ckb_cli.wallet_get_capacity(self.account1["address"]["testnet"])
    #     after_balance2 = self.Ckb_cli.wallet_get_capacity(
    #         self.account2["address"]["testnet"]
    #     )
    #     print("before_balance1:", before_balance1)
    #     print("before_balance2:", before_balance2)
    #     print("after_balance1:", after_balance1)
    #     print("after_balance2:", after_balance2)
    #     assert after_balance2 - before_balance2 == 162

    # def test_commitment_fee_rate_very_big(self):
    #     """
    #     commitment_fee_rate == int.max
    #     Returns:
    #
    #         TODO : 思考commit ment fee 的测试用例
    #     """
    #     self.fiber1.connect_peer(self.fiber2)
    #     time.sleep(5)
    #     with pytest.raises(Exception) as exc_info:
    #         temporary_channel_id = self.fiber1.get_client().open_channel(
    #             {
    #                 "peer_id": self.fiber2.get_peer_id(),
    #                 "funding_amount": hex(200 * 100000000),
    #                 "public": True,
    #                 "commitment_fee_rate": hex(18446744073709551615),
    #                 # "tlc_fee_proportional_millionths": "0x4B0",
    #
    #             }
    #         )
    #     expected_error_message = (
    #         "expect more CKB amount as reserved ckb amount"
    #     )
    #     assert expected_error_message in exc_info.value.args[0], (
    #         f"Expected substring '{expected_error_message}' "
    #         f"not found in actual string '{exc_info.value.args[0]}'"
    #     )
    #
    # def test_commitment_fee_rate_exist(self):
    #     """
    #     commitment_fee_rate != default.value
    #     Returns:
    #     """
    #
    # def test_commitment_fee_rate_zero(self):
    #     """
    #     commitment_fee_rate == 0
    #     Returns:
    #     """
    #     self.fiber1.connect_peer(self.fiber2)
    #     time.sleep(5)
    #     with pytest.raises(Exception) as exc_info:
    #         temporary_channel_id = self.fiber1.get_client().open_channel(
    #             {
    #                 "peer_id": self.fiber2.get_peer_id(),
    #                 "funding_amount": hex(200 * 100000000),
    #                 "public": True,
    #                 "commitment_fee_rate": hex(0),
    #                 # "tlc_fee_proportional_millionths": "0x4B0",
    #
    #             }
    #         )
    #     expected_error_message = (
    #         "Commitment fee rate is less than 1000"
    #     )
    #     assert expected_error_message in exc_info.value.args[0], (
    #         f"Expected substring '{expected_error_message}' "
    #         f"not found in actual string '{exc_info.value.args[0]}'"
    #     )
    #
    # def test_commitment_fee_rate_is_1(self):
    #     """
    #      commitment_fee_rate == 1
    #     Returns:
    #     Returns:
    #
    #     """
    #     self.fiber1.connect_peer(self.fiber2)
    #     time.sleep(5)
    #     with pytest.raises(Exception) as exc_info:
    #         temporary_channel_id = self.fiber1.get_client().open_channel(
    #             {
    #                 "peer_id": self.fiber2.get_peer_id(),
    #                 "funding_amount": hex(200 * 100000000),
    #                 "public": True,
    #                 "commitment_fee_rate": hex(1),
    #                 # "tlc_fee_proportional_millionths": "0x4B0",
    #
    #             }
    #         )
    #     expected_error_message = (
    #         "Commitment fee rate is less than 1000"
    #     )
    #     assert expected_error_message in exc_info.value.args[0], (
    #         f"Expected substring '{expected_error_message}' "
    #         f"not found in actual string '{exc_info.value.args[0]}'"
    #     )

    # def test_funding_fee_rate_none(self):
    #     """
    #     funding_fee_rate is none
    #     Returns:
    #     """
    #     self.test_linked_peer()
    #
    # def test_funding_fee_rate_too_min(self):
    #     """
    #     funding_fee_rate = 1
    #     Returns:
    #     """
    #     self.fiber1.connect_peer(self.fiber2)
    #     time.sleep(5)
    #     with pytest.raises(Exception) as exc_info:
    #         temporary_channel_id = self.fiber1.get_client().open_channel(
    #             {
    #                 "peer_id": self.fiber2.get_peer_id(),
    #                 "funding_amount": hex(200 * 100000000),
    #                 "public": True,
    #                 "funding_fee_rate": hex(1),
    #                 # "tlc_fee_proportional_millionths": "0x4B0",
    #
    #             }
    #         )
    #     expected_error_message = (
    #         "Funding fee rate is less than 1000"
    #     )
    #     assert expected_error_message in exc_info.value.args[0], (
    #         f"Expected substring '{expected_error_message}' "
    #         f"not found in actual string '{exc_info.value.args[0]}'"
    #     )
    #
    # def test_funding_fee_rate_too_big(self):
    #     """
    #     funding_fee_rate  == int.max
    #     Returns:
    #     """
    #     self.fiber1.connect_peer(self.fiber2)
    #     time.sleep(5)
    #     temporary_channel_id = self.fiber1.get_client().open_channel(
    #         {
    #             "peer_id": self.fiber2.get_peer_id(),
    #             "funding_amount": hex(200 * 100000000),
    #             "public": True,
    #             "funding_fee_rate": "0xffffffffffffffff",
    #             # "tlc_fee_proportional_millionths": "0x4B0",
    #
    #         }
    #     )
    #     time.sleep(1)
    #     wait_for_channel_state(
    #         self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
    #     )
    #     time.sleep(5)
    #     # transfer
    #     self.fiber1.get_client().graph_channels()
    #     self.fiber1.get_client().graph_nodes()
    #     payment_preimage = generate_random_preimage()
    #     invoice_balance = 100 * 100000000
    #     invoice = self.fiber2.get_client().new_invoice(
    #         {
    #             "amount": hex(invoice_balance),
    #             "currency": "Fibb",
    #             "description": "test invoice generated by node2",
    #             "expiry": "0xe10",
    #             "final_cltv": "0x28",
    #             "payment_preimage": payment_preimage,
    #             "hash_algorithm": "sha256",
    #         }
    #     )
    #     before_channel = self.fiber1.get_client().list_channels({})
    #
    #     self.fiber1.get_client().send_payment(
    #         {
    #             "invoice": invoice["invoice_address"],
    #         }
    #     )
    #     time.sleep(10)
    #     after_channel = self.fiber1.get_client().list_channels({})
    #     assert (
    #             int(before_channel["channels"][0]["local_balance"], 16)
    #             - int(after_channel["channels"][0]["local_balance"], 16)
    #             == invoice_balance
    #     )
    #
    #     channels = self.fiber1.get_client().list_channels(
    #         {"peer_id": self.fiber2.get_peer_id()}
    #     )
    #     N1N2_CHANNEL_ID = channels["channels"][0]["channel_id"]
    #     self.fiber1.get_client().graph_channels()
    #
    #     before_balance1 = self.Ckb_cli.wallet_get_capacity(
    #         self.account1["address"]["testnet"]
    #     )
    #     before_balance2 = self.Ckb_cli.wallet_get_capacity(
    #         self.account2["address"]["testnet"]
    #     )
    #     # shut down
    #     self.fiber1.get_client().shutdown_channel(
    #         {
    #             "channel_id": N1N2_CHANNEL_ID,
    #             "close_script": {
    #                 "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
    #                 "hash_type": "type",
    #                 "args": self.account1["lock_arg"],
    #             },
    #             "fee_rate": "0x3FC",
    #         }
    #     )
    #     # todo wait close tx commit
    #     time.sleep(20)
    #     after_balance1 = self.Ckb_cli.wallet_get_capacity(self.account1["address"]["testnet"])
    #     after_balance2 = self.Ckb_cli.wallet_get_capacity(
    #         self.account2["address"]["testnet"]
    #     )
    #     print("before_balance1:", before_balance1)
    #     print("before_balance2:", before_balance2)
    #     print("after_balance1:", after_balance1)
    #     print("after_balance2:", after_balance2)
    #     assert after_balance2 - before_balance2 == 162
    #
    # def test_funding_fee_rate_over_flow(self):
    #     """
    #     funding_fee_rate > int.max
    #     Returns:
    #     """
    #     self.fiber1.connect_peer(self.fiber2)
    #     time.sleep(5)
    #     with pytest.raises(Exception) as exc_info:
    #         temporary_channel_id = self.fiber1.get_client().open_channel(
    #             {
    #                 "peer_id": self.fiber2.get_peer_id(),
    #                 "funding_amount": hex(200 * 100000000),
    #                 "public": True,
    #                 "funding_fee_rate": "0xfffffffffffffffffffffffff",
    #                 # "tlc_fee_proportional_millionths": "0x4B0",
    #
    #             }
    #         )
    #     expected_error_message = (
    #         "Invalid params"
    #     )
    #     assert expected_error_message in exc_info.value.args[0], (
    #         f"Expected substring '{expected_error_message}' "
    #         f"not found in actual string '{exc_info.value.args[0]}'"
    #     )
    #
    # def test_funding_fee_rate_not_eq_default(self):
    #     """
    #     funding_fee_rate != default value
    #     Returns:
    #     """
    #     self.fiber1.connect_peer(self.fiber2)
    #     time.sleep(5)
    #     temporary_channel_id = self.fiber1.get_client().open_channel(
    #         {
    #             "peer_id": self.fiber2.get_peer_id(),
    #             "funding_amount": hex(200 * 100000000),
    #             "public": True,
    #             "funding_fee_rate": "0xffff",
    #             # "tlc_fee_proportional_millionths": "0x4B0",
    #
    #         }
    #     )
    #     time.sleep(1)
    #     wait_for_channel_state(
    #         self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
    #     )
    #     time.sleep(5)
    #     # transfer
    #     self.fiber1.get_client().graph_channels()
    #     self.fiber1.get_client().graph_nodes()
    #     payment_preimage = generate_random_preimage()
    #     invoice_balance = 100 * 100000000
    #     invoice = self.fiber2.get_client().new_invoice(
    #         {
    #             "amount": hex(invoice_balance),
    #             "currency": "Fibb",
    #             "description": "test invoice generated by node2",
    #             "expiry": "0xe10",
    #             "final_cltv": "0x28",
    #             "payment_preimage": payment_preimage,
    #             "hash_algorithm": "sha256",
    #         }
    #     )
    #     before_channel = self.fiber1.get_client().list_channels({})
    #
    #     self.fiber1.get_client().send_payment(
    #         {
    #             "invoice": invoice["invoice_address"],
    #         }
    #     )
    #     time.sleep(10)
    #     after_channel = self.fiber1.get_client().list_channels({})
    #     assert (
    #             int(before_channel["channels"][0]["local_balance"], 16)
    #             - int(after_channel["channels"][0]["local_balance"], 16)
    #             == invoice_balance
    #     )
    #
    #     channels = self.fiber1.get_client().list_channels(
    #         {"peer_id": self.fiber2.get_peer_id()}
    #     )
    #     N1N2_CHANNEL_ID = channels["channels"][0]["channel_id"]
    #     self.fiber1.get_client().graph_channels()
    #
    #     before_balance1 = self.Ckb_cli.wallet_get_capacity(
    #         self.account1["address"]["testnet"]
    #     )
    #     before_balance2 = self.Ckb_cli.wallet_get_capacity(
    #         self.account2["address"]["testnet"]
    #     )
    #     # shut down
    #     self.fiber1.get_client().shutdown_channel(
    #         {
    #             "channel_id": N1N2_CHANNEL_ID,
    #             "close_script": {
    #                 "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
    #                 "hash_type": "type",
    #                 "args": self.account1["lock_arg"],
    #             },
    #             "fee_rate": "0x3FC",
    #         }
    #     )
    #     # todo wait close tx commit
    #     time.sleep(20)
    #     after_balance1 = self.Ckb_cli.wallet_get_capacity(self.account1["address"]["testnet"])
    #     after_balance2 = self.Ckb_cli.wallet_get_capacity(
    #         self.account2["address"]["testnet"]
    #     )
    #     print("before_balance1:", before_balance1)
    #     print("before_balance2:", before_balance2)
    #     print("after_balance1:", after_balance1)
    #     print("after_balance2:", after_balance2)
    #     assert after_balance2 - before_balance2 == 162
    #
    # def test_funding_fee_rate_gt_balance(self):
    #     """
    #     todo: 需要失败的状态
    #     Returns:
    #     """
    #     account3_private_key = "0x200c06bfd800d27397002dca6fb0993d5ba6399b4238b2f29ee9deb97593d2b1"
    #     account3 = self.Ckb_cli.util_key_info_by_private_key(account3_private_key)
    #     tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(self.Config.ACCOUNT_PRIVATE_1,
    #                                                           account3["address"]["testnet"],
    #                                                           1000,
    #                                                           self.node.rpcUrl)
    #     self.Miner.miner_until_tx_committed(self.node, tx_hash)
    #
    #     # start fiber3
    #     self.fiber3 = Fiber.init_by_port(
    #         FiberConfigPath.V100_DEV,
    #         account3_private_key,
    #         "fiber/node3",
    #         "8231",
    #         "8232",
    #     )
    #     self.fibers.append(self.fiber3)
    #     self.fiber3.prepare(
    #         update_config={
    #             "ckb_rpc_url": self.node.rpcUrl,
    #         }
    #     )
    #     self.fiber3.start(self.node)
    #     self.fiber3.connect_peer(self.fiber2)
    #     time.sleep(3)
    #     self.fiber3.get_client().open_channel({
    #
    #         "peer_id": self.fiber2.get_peer_id(),
    #         "funding_amount": hex(990 * 100000000),
    #         "public": True,
    #         "funding_fee_rate": "0xffffffffff",
    #
    #         # "tlc_fee_proportional_millionths": "0x4B0",
    #
    #     })
    #     time.sleep(1)
    #     wait_for_channel_state(
    #         self.fiber3.get_client(), self.fiber2.get_peer_id(), "NEGOTIATING_FUNDING", 120
    #     )

    # def test_tlc_locktime_expiry_delta_none(self):
    #     """
    #     tlc_locktime_expiry_delta = none
    #     Returns:
    #     """
    #     self.test_linked_peer()
    #
    # def test_tlc_locktime_expiry_delta_is_zero(self):
    #     """
    #     tlc_locktime_expiry_delta = 0
    #     Returns:
    #     """
    #     self.fiber1.connect_peer(self.fiber2)
    #     time.sleep(5)
    #     temporary_channel_id = self.fiber1.get_client().open_channel(
    #         {
    #             "peer_id": self.fiber2.get_peer_id(),
    #             "funding_amount": hex(200 * 100000000),
    #             "public": True,
    #             "tlc_locktime_expiry_delta": "0x0",
    #             # "tlc_fee_proportional_millionths": "0x4B0",
    #
    #         }
    #     )
    #     time.sleep(1)
    #     wait_for_channel_state(
    #         self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
    #     )
    #     time.sleep(5)
    #     # transfer
    #     self.fiber1.get_client().graph_channels()
    #     self.fiber1.get_client().graph_nodes()
    #     payment_preimage = generate_random_preimage()
    #     invoice_balance = 100 * 100000000
    #     invoice = self.fiber2.get_client().new_invoice(
    #         {
    #             "amount": hex(invoice_balance),
    #             "currency": "Fibb",
    #             "description": "test invoice generated by node2",
    #             "expiry": "0xe10",
    #             "final_cltv": "0x28",
    #             "payment_preimage": payment_preimage,
    #             "hash_algorithm": "sha256",
    #         }
    #     )
    #     before_channel = self.fiber1.get_client().list_channels({})
    #
    #     self.fiber1.get_client().send_payment(
    #         {
    #             "invoice": invoice["invoice_address"],
    #         }
    #     )
    #     time.sleep(10)
    #     after_channel = self.fiber1.get_client().list_channels({})
    #     assert (
    #             int(before_channel["channels"][0]["local_balance"], 16)
    #             - int(after_channel["channels"][0]["local_balance"], 16)
    #             == invoice_balance
    #     )
    #
    #     channels = self.fiber1.get_client().list_channels(
    #         {"peer_id": self.fiber2.get_peer_id()}
    #     )
    #     N1N2_CHANNEL_ID = channels["channels"][0]["channel_id"]
    #     self.fiber1.get_client().graph_channels()
    #
    #     before_balance1 = self.Ckb_cli.wallet_get_capacity(
    #         self.account1["address"]["testnet"]
    #     )
    #     before_balance2 = self.Ckb_cli.wallet_get_capacity(
    #         self.account2["address"]["testnet"]
    #     )
    #     # shut down
    #     self.fiber1.get_client().shutdown_channel(
    #         {
    #             "channel_id": N1N2_CHANNEL_ID,
    #             "close_script": {
    #                 "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
    #                 "hash_type": "type",
    #                 "args": self.account1["lock_arg"],
    #             },
    #             "fee_rate": "0x3FC",
    #         }
    #     )
    #     # todo wait close tx commit
    #     time.sleep(20)
    #     after_balance1 = self.Ckb_cli.wallet_get_capacity(self.account1["address"]["testnet"])
    #     after_balance2 = self.Ckb_cli.wallet_get_capacity(
    #         self.account2["address"]["testnet"]
    #     )
    #     print("before_balance1:", before_balance1)
    #     print("before_balance2:", before_balance2)
    #     print("after_balance1:", after_balance1)
    #     print("after_balance2:", after_balance2)
    #     assert after_balance2 - before_balance2 == 162
    #
    # def test_tlc_locktime_expiry_delta_is_1(self):
    #     """
    #     tlc_locktime_expiry_delta = 1
    #     Returns:
    #     todo:
    #         qa: open_channel 的 tlc_locktime_expiry_delta 作用是什么呢？ 有点没理解 @by  我要怎么才能测到这个参数
    #          A 给 B 发送一个 tlc，如果 B 知道原相，那 B 可以取走 tlc 里面的资金，否则过了时间 tlc_locktime_expiry_delta 之后，A 可以取回 tlc 里面的资金。
    #         那a 可以怎么取回tlc的资金
    #         要在 watchtower 里面做，我们现在似乎没有这个功能
    #     """
    #
    # def test_tlc_locktime_expiry_delta_not_eq_default(self):
    #     """
    #     tlc_locktime_expiry_delta != default
    #
    #     Returns:
    #
    #     """

    # def test_tlc_min_value_none(self):
    #     """
    #     tlc_min_value = none
    #     default is 0
    #     Returns:
    #     """
    #     self.fiber1.connect_peer(self.fiber2)
    #     time.sleep(5)
    #     temporary_channel_id = self.fiber1.get_client().open_channel(
    #         {
    #             "peer_id": self.fiber2.get_peer_id(),
    #             "funding_amount": hex(200 * 100000000),
    #             "public": True,
    #             # "funding_fee_rate": "0xffff",
    #             # "tlc_fee_proportional_millionths": "0x4B0",
    #
    #         }
    #     )
    #     time.sleep(1)
    #     wait_for_channel_state(
    #         self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
    #     )
    #     time.sleep(5)
    #     # transfer
    #     self.fiber1.get_client().graph_channels()
    #     self.fiber1.get_client().graph_nodes()
    #     payment_preimage = generate_random_preimage()
    #     channels = self.fiber1.get_client().list_channels({})
    #     invoice_balance = channels["channels"][0]['local_balance']
    #
    #     invoice = self.fiber2.get_client().new_invoice(
    #         {
    #             "amount": invoice_balance,
    #             "currency": "Fibb",
    #             "description": "test invoice generated by node2",
    #             "expiry": "0xe10",
    #             "final_cltv": "0x28",
    #             "payment_preimage": payment_preimage,
    #             "hash_algorithm": "sha256",
    #         }
    #     )
    #     before_channel = self.fiber1.get_client().list_channels({})
    #
    #     self.fiber1.get_client().send_payment(
    #         {
    #             "invoice": invoice["invoice_address"],
    #         }
    #     )
    #     time.sleep(10)
    #     after_channel = self.fiber1.get_client().list_channels({})
    #     assert (
    #             int(before_channel["channels"][0]["local_balance"], 16)
    #             - int(after_channel["channels"][0]["local_balance"], 16)
    #             == int(invoice_balance, 16)
    #     )
    #
    #     channels = self.fiber1.get_client().list_channels(
    #         {"peer_id": self.fiber2.get_peer_id()}
    #     )
    #     N1N2_CHANNEL_ID = channels["channels"][0]["channel_id"]
    #     self.fiber1.get_client().graph_channels()
    #
    #     before_balance1 = self.Ckb_cli.wallet_get_capacity(
    #         self.account1["address"]["testnet"]
    #     )
    #     before_balance2 = self.Ckb_cli.wallet_get_capacity(
    #         self.account2["address"]["testnet"]
    #     )
    #     # shut down
    #     self.fiber1.get_client().shutdown_channel(
    #         {
    #             "channel_id": N1N2_CHANNEL_ID,
    #             "close_script": {
    #                 "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
    #                 "hash_type": "type",
    #                 "args": self.account1["lock_arg"],
    #             },
    #             "fee_rate": "0x3FC",
    #         }
    #     )
    #     # todo wait close tx commit
    #     time.sleep(20)
    #     after_balance1 = self.Ckb_cli.wallet_get_capacity(self.account1["address"]["testnet"])
    #     after_balance2 = self.Ckb_cli.wallet_get_capacity(
    #         self.account2["address"]["testnet"]
    #     )
    #     print("before_balance1:", before_balance1)
    #     print("before_balance2:", before_balance2)
    #     print("after_balance1:", after_balance1)
    #     print("after_balance2:", after_balance2)
    #     assert after_balance2 - before_balance2 == 200
    #
    # def test_tlc_min_value_is_not_zero(self):
    #     """
    #     tlc_min_value != 0
    #     tlc_min_value limit: fee+ amount
    #     Returns:
    #
    #     """
    #     self.fiber1.connect_peer(self.fiber2)
    #     time.sleep(5)
    #     temporary_channel_id = self.fiber1.get_client().open_channel(
    #         {
    #             "peer_id": self.fiber2.get_peer_id(),
    #             "funding_amount": hex(200 * 100000000),
    #             "public": True,
    #             "tlc_min_value": hex(2 * 100000000)
    #             # "funding_fee_rate": "0xffff",
    #             # "tlc_fee_proportional_millionths": "0x4B0",
    #
    #         }
    #     )
    #     time.sleep(1)
    #     wait_for_channel_state(
    #         self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
    #     )
    #     time.sleep(5)
    #     # transfer
    #     self.fiber1.get_client().graph_channels()
    #     self.fiber1.get_client().graph_nodes()
    #     payment_preimage = generate_random_preimage()
    #     channels = self.fiber1.get_client().list_channels({})
    #     invoice_balance = hex(100 * 100000000)
    #
    #     invoice = self.fiber2.get_client().new_invoice(
    #         {
    #             "amount": invoice_balance,
    #             "currency": "Fibb",
    #             "description": "test invoice generated by node2",
    #             "expiry": "0xe10",
    #             "final_cltv": "0x28",
    #             "payment_preimage": payment_preimage,
    #             "hash_algorithm": "sha256",
    #         }
    #     )
    #     before_channel = self.fiber1.get_client().list_channels({})
    #
    #     self.fiber1.get_client().send_payment(
    #         {
    #             "invoice": invoice["invoice_address"],
    #         }
    #     )
    #     time.sleep(10)
    #     after_channel = self.fiber1.get_client().list_channels({})
    #     assert (
    #             int(before_channel["channels"][0]["local_balance"], 16)
    #             - int(after_channel["channels"][0]["local_balance"], 16)
    #             == int(invoice_balance, 16)
    #     )
    #
    #     # node2 send 2 ckb
    #     invoice_balance = hex(2 * 100000000)
    #     payment_preimage = generate_random_preimage()
    #     invoice = self.fiber1.get_client().new_invoice(
    #         {
    #             "amount": invoice_balance,
    #             "currency": "Fibb",
    #             "description": "test invoice generated by node2",
    #             "expiry": "0xe10",
    #             "final_cltv": "0x28",
    #             "payment_preimage": payment_preimage,
    #             "hash_algorithm": "sha256",
    #         }
    #     )
    #     before_channel = self.fiber2.get_client().list_channels({})
    #
    #     self.fiber2.get_client().send_payment(
    #         {
    #             "invoice": invoice["invoice_address"],
    #         }
    #     )
    #     time.sleep(10)
    #     after_channel = self.fiber2.get_client().list_channels({})
    #     assert (
    #             int(before_channel["channels"][0]["local_balance"], 16)
    #             - int(after_channel["channels"][0]["local_balance"], 16)
    #             == int(invoice_balance, 16)
    #     )
    #
    #     # node2 send 1 ckb
    #
    #     invoice_balance = hex(2 * 100000000 - 1 - 200000)
    #     payment_preimage = generate_random_preimage()
    #     invoice = self.fiber1.get_client().new_invoice(
    #         {
    #             "amount": invoice_balance,
    #             "currency": "Fibb",
    #             "description": "test invoice generated by node2",
    #             "expiry": "0xe10",
    #             "final_cltv": "0x28",
    #             "payment_preimage": payment_preimage,
    #             "hash_algorithm": "sha256",
    #         }
    #     )
    #     before_channel = self.fiber2.get_client().list_channels({})
    #     print("node2 send 1 ckb failed ")
    #     with pytest.raises(Exception) as exc_info:
    #         self.fiber2.get_client().send_payment(
    #             {
    #                 "invoice": invoice["invoice_address"],
    #             }
    #         )
    #     expected_error_message = (
    #         "Failed to build route"
    #     )
    #     assert expected_error_message in exc_info.value.args[0], (
    #         f"Expected substring '{expected_error_message}' "
    #         f"not found in actual string '{exc_info.value.args[0]}'"
    #     )
    #
    #     channels = self.fiber1.get_client().list_channels(
    #         {"peer_id": self.fiber2.get_peer_id()}
    #     )
    #     N1N2_CHANNEL_ID = channels["channels"][0]["channel_id"]
    #     self.fiber1.get_client().graph_channels()
    #
    #     before_balance1 = self.Ckb_cli.wallet_get_capacity(
    #         self.account1["address"]["testnet"]
    #     )
    #     before_balance2 = self.Ckb_cli.wallet_get_capacity(
    #         self.account2["address"]["testnet"]
    #     )
    #     # shut down
    #     self.fiber1.get_client().shutdown_channel(
    #         {
    #             "channel_id": N1N2_CHANNEL_ID,
    #             "close_script": {
    #                 "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
    #                 "hash_type": "type",
    #                 "args": self.account1["lock_arg"],
    #             },
    #             "fee_rate": "0x3FC",
    #         }
    #     )
    #     # todo wait close tx commit
    #     time.sleep(20)
    #     after_balance1 = self.Ckb_cli.wallet_get_capacity(self.account1["address"]["testnet"])
    #     after_balance2 = self.Ckb_cli.wallet_get_capacity(
    #         self.account2["address"]["testnet"]
    #     )
    #     print("before_balance1:", before_balance1)
    #     print("before_balance2:", before_balance2)
    #     print("after_balance1:", after_balance1)
    #     print("after_balance2:", after_balance2)
    #     assert after_balance2 - before_balance2 == 160
    #
    # def test_tlc_min_value_gt_funding_amount(self):
    #     """
    #     tlc_min_value > funding_amount
    #     Returns:
    #     """
    #     self.fiber1.connect_peer(self.fiber2)
    #     time.sleep(5)
    #     temporary_channel_id = self.fiber1.get_client().open_channel(
    #         {
    #             "peer_id": self.fiber2.get_peer_id(),
    #             "funding_amount": hex(200 * 100000000),
    #             "public": True,
    #             "tlc_min_value": hex(210 * 100000000)
    #             # "funding_fee_rate": "0xffff",
    #             # "tlc_fee_proportional_millionths": "0x4B0",
    #
    #         }
    #     )
    #     time.sleep(1)
    #     wait_for_channel_state(
    #         self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
    #     )
    #     time.sleep(5)
    #     # transfer
    #     self.fiber1.get_client().graph_channels()
    #     self.fiber1.get_client().graph_nodes()
    #     payment_preimage = generate_random_preimage()
    #     channels = self.fiber1.get_client().list_channels({})
    #     invoice_balance = channels["channels"][0]['local_balance']
    #
    #     invoice = self.fiber2.get_client().new_invoice(
    #         {
    #             "amount": invoice_balance,
    #             "currency": "Fibb",
    #             "description": "test invoice generated by node2",
    #             "expiry": "0xe10",
    #             "final_cltv": "0x28",
    #             "payment_preimage": payment_preimage,
    #             "hash_algorithm": "sha256",
    #         }
    #     )
    #     before_channel = self.fiber1.get_client().list_channels({})
    #
    #     self.fiber1.get_client().send_payment(
    #         {
    #             "invoice": invoice["invoice_address"],
    #         }
    #     )
    #     time.sleep(10)
    #     after_channel = self.fiber1.get_client().list_channels({})
    #     assert (
    #             int(before_channel["channels"][0]["local_balance"], 16)
    #             - int(after_channel["channels"][0]["local_balance"], 16)
    #             == int(invoice_balance, 16)
    #     )
    #
    #     # node2 send all ckb to node 1
    #
    #     invoice_balance = channels["channels"][0]['local_balance']
    #     payment_preimage = generate_random_preimage()
    #     invoice = self.fiber1.get_client().new_invoice(
    #         {
    #             "amount": invoice_balance,
    #             "currency": "Fibb",
    #             "description": "test invoice generated by node2",
    #             "expiry": "0xe10",
    #             "final_cltv": "0x28",
    #             "payment_preimage": payment_preimage,
    #             "hash_algorithm": "sha256",
    #         }
    #     )
    #     before_channel = self.fiber2.get_client().list_channels({})
    #     print("node2 send 1 ckb failed ")
    #     with pytest.raises(Exception) as exc_info:
    #         self.fiber2.get_client().send_payment(
    #             {
    #                 "invoice": invoice["invoice_address"],
    #             }
    #         )
    #     expected_error_message = (
    #         "no path found"
    #     )
    #     assert expected_error_message in exc_info.value.args[0], (
    #         f"Expected substring '{expected_error_message}' "
    #         f"not found in actual string '{exc_info.value.args[0]}'"
    #     )
    #
    #     channels = self.fiber1.get_client().list_channels(
    #         {"peer_id": self.fiber2.get_peer_id()}
    #     )
    #     N1N2_CHANNEL_ID = channels["channels"][0]["channel_id"]
    #     self.fiber1.get_client().graph_channels()
    #
    #     before_balance1 = self.Ckb_cli.wallet_get_capacity(
    #         self.account1["address"]["testnet"]
    #     )
    #     before_balance2 = self.Ckb_cli.wallet_get_capacity(
    #         self.account2["address"]["testnet"]
    #     )
    #     # shut down
    #     self.fiber2.get_client().shutdown_channel(
    #         {
    #             "channel_id": N1N2_CHANNEL_ID,
    #             "close_script": {
    #                 "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
    #                 "hash_type": "type",
    #                 "args": self.account2["lock_arg"],
    #             },
    #             "fee_rate": "0x3FC",
    #         }
    #     )
    #     # todo wait close tx commit
    #     time.sleep(20)
    #     after_balance1 = self.Ckb_cli.wallet_get_capacity(self.account1["address"]["testnet"])
    #     after_balance2 = self.Ckb_cli.wallet_get_capacity(
    #         self.account2["address"]["testnet"]
    #     )
    #     print("before_balance1:", before_balance1)
    #     print("before_balance2:", before_balance2)
    #     print("after_balance1:", after_balance1)
    #     print("after_balance2:", after_balance2)
    #     assert after_balance2 - before_balance2 == 162
    #
    # def test_ckb_tlc_min_value_not_eq_default(self):
    #     """
    #     tlc_min_value != default
    #     Returns:
    #     """
    #     self.test_tlc_min_value_is_not_zero()
    #
    # def test_udt_tlc_min_value_not_eq_default(self):
    #     """
    #     tlc_min_value != default
    #     Returns:
    #     """
    #     self.fiber1.connect_peer(self.fiber2)
    #     time.sleep(5)
    #     self.fiber1.get_client().open_channel(
    #         {
    #             "peer_id": self.fiber2.get_peer_id(),
    #             "funding_amount": hex(1000 * 100000000),
    #             "public": True,
    #             "tlc_min_value": hex(160 * 100000000),
    #             "funding_udt_type_script": {
    #                 "code_hash": self.udtContract.get_code_hash(True, self.node.rpcUrl),
    #                 "hash_type": "type",
    #                 "args": self.udtContract.get_owner_arg_by_lock_arg(self.account1["lock_arg"]),
    #             },
    #             # "tlc_fee_proportional_millionths": "0x4B0",
    #         }
    #     )
    #
    #     time.sleep(1)
    #     wait_for_channel_state(
    #         self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
    #     )
    #     time.sleep(5)
    #     # transfer
    #     self.fiber1.get_client().graph_channels()
    #     self.fiber1.get_client().graph_nodes()
    #     payment_preimage = generate_random_preimage()
    #     channels = self.fiber1.get_client().list_channels({})
    #     invoice_balance = hex(500 * 100000000)
    #
    #     invoice = self.fiber2.get_client().new_invoice(
    #         {
    #             "amount": invoice_balance,
    #             "currency": "Fibb",
    #             "description": "test invoice generated by node2",
    #             "expiry": "0xe10",
    #             "final_cltv": "0x28",
    #             "payment_preimage": payment_preimage,
    #             "hash_algorithm": "sha256",
    #             "udt_type_script": {
    #                 "code_hash": self.udtContract.get_code_hash(True, self.node.rpcUrl),
    #                 "hash_type": "type",
    #                 "args": self.udtContract.get_owner_arg_by_lock_arg(self.account1["lock_arg"]),
    #             },
    #         }
    #     )
    #     before_channel = self.fiber1.get_client().list_channels({})
    #
    #     self.fiber1.get_client().send_payment(
    #         {
    #             "invoice": invoice["invoice_address"],
    #         }
    #     )
    #     time.sleep(10)
    #     after_channel = self.fiber1.get_client().list_channels({})
    #     assert (
    #             int(before_channel["channels"][0]["local_balance"], 16)
    #             - int(after_channel["channels"][0]["local_balance"], 16)
    #             == int(invoice_balance, 16)
    #     )
    #
    #     # node2 send 160 udt
    #     invoice_balance = hex(160 * 100000000)
    #     payment_preimage = generate_random_preimage()
    #     invoice = self.fiber1.get_client().new_invoice(
    #         {
    #             "amount": invoice_balance,
    #             "currency": "Fibb",
    #             "description": "test invoice generated by node2",
    #             "expiry": "0xe10",
    #             "final_cltv": "0x28",
    #             "payment_preimage": payment_preimage,
    #             "hash_algorithm": "sha256",
    #             "udt_type_script": {
    #                 "code_hash": self.udtContract.get_code_hash(True, self.node.rpcUrl),
    #                 "hash_type": "type",
    #                 "args": self.udtContract.get_owner_arg_by_lock_arg(self.account1["lock_arg"]),
    #             },
    #         }
    #     )
    #     before_channel = self.fiber2.get_client().list_channels({})
    #
    #     self.fiber2.get_client().send_payment(
    #         {
    #             "invoice": invoice["invoice_address"],
    #         }
    #     )
    #     time.sleep(10)
    #     after_channel = self.fiber2.get_client().list_channels({})
    #     assert (
    #             int(before_channel["channels"][0]["local_balance"], 16)
    #             - int(after_channel["channels"][0]["local_balance"], 16)
    #             == int(invoice_balance, 16)
    #     )
    #
    #     # node2 send 1 ckb
    #
    #     invoice_balance = hex(160 * 100000000 - 16000000)
    #     payment_preimage = generate_random_preimage()
    #     invoice = self.fiber1.get_client().new_invoice(
    #         {
    #             "amount": invoice_balance,
    #             "currency": "Fibb",
    #             "description": "test invoice generated by node2",
    #             "expiry": "0xe10",
    #             "final_cltv": "0x28",
    #             "payment_preimage": payment_preimage,
    #             "hash_algorithm": "sha256",
    #             "udt_type_script": {
    #                 "code_hash": self.udtContract.get_code_hash(True, self.node.rpcUrl),
    #                 "hash_type": "type",
    #                 "args": self.udtContract.get_owner_arg_by_lock_arg(self.account1["lock_arg"]),
    #             },
    #         }
    #     )
    #     before_channel = self.fiber2.get_client().list_channels({})
    #     print("node2 send 1 ckb failed ")
    #     with pytest.raises(Exception) as exc_info:
    #         self.fiber2.get_client().send_payment(
    #             {
    #                 "invoice": invoice["invoice_address"],
    #             }
    #         )
    #     expected_error_message = (
    #         "no path found"
    #     )
    #     assert expected_error_message in exc_info.value.args[0], (
    #         f"Expected substring '{expected_error_message}' "
    #         f"not found in actual string '{exc_info.value.args[0]}'"
    #     )
    #
    #     channels = self.fiber1.get_client().list_channels(
    #         {"peer_id": self.fiber2.get_peer_id()}
    #     )
    #     N1N2_CHANNEL_ID = channels["channels"][0]["channel_id"]
    #     self.fiber1.get_client().graph_channels()
    #
    #     before_balance1 = self.Ckb_cli.wallet_get_capacity(
    #         self.account1["address"]["testnet"]
    #     )
    #     before_balance2 = self.Ckb_cli.wallet_get_capacity(
    #         self.account2["address"]["testnet"]
    #     )
    #     # shut down
    #     self.fiber1.get_client().shutdown_channel(
    #         {
    #             "channel_id": N1N2_CHANNEL_ID,
    #             "close_script": {
    #                 "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
    #                 "hash_type": "type",
    #                 "args": self.account1["lock_arg"],
    #             },
    #             "fee_rate": "0x3FC",
    #         }
    #     )
    #     # todo wait close tx commit
    #     time.sleep(20)
    #     after_balance1 = self.Ckb_cli.wallet_get_capacity(self.account1["address"]["testnet"])
    #     after_balance2 = self.Ckb_cli.wallet_get_capacity(
    #         self.account2["address"]["testnet"]
    #     )
    #     print("before_balance1:", before_balance1)
    #     print("before_balance2:", before_balance2)
    #     print("after_balance1:", after_balance1)
    #     print("after_balance2:", after_balance2)
    #
    # def test_ckb_tlc_min_value_gt_tlc_max_value(self):
    #     pass
    #
    # def test_udt_tlc_min_value_gt_tlc_max_value(self):
    #     """
    #     tlc_min_value > tlc_max_value
    #     Returns:
    #     """
    #     self.fiber1.connect_peer(self.fiber2)
    #     time.sleep(5)
    #     self.fiber1.get_client().open_channel(
    #         {
    #             "peer_id": self.fiber2.get_peer_id(),
    #             "funding_amount": hex(1000 * 100000000),
    #             "public": True,
    #             "tlc_min_value": hex(160 * 100000000),
    #             "tlc_max_value": hex(160 * 100000000 - 1),
    #             "funding_udt_type_script": {
    #                 "code_hash": self.udtContract.get_code_hash(True, self.node.rpcUrl),
    #                 "hash_type": "type",
    #                 "args": self.udtContract.get_owner_arg_by_lock_arg(self.account1["lock_arg"]),
    #             },
    #             # "tlc_fee_proportional_millionths": "0x4B0",
    #         }
    #     )
    #
    #     time.sleep(1)
    #     wait_for_channel_state(
    #         self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
    #     )
    #     time.sleep(5)
    #     # transfer
    #     self.fiber1.get_client().graph_channels()
    #     self.fiber1.get_client().graph_nodes()
    #     payment_preimage = generate_random_preimage()
    #     channels = self.fiber1.get_client().list_channels({})
    #     invoice_balance = hex(500 * 100000000)
    #
    #     invoice = self.fiber2.get_client().new_invoice(
    #         {
    #             "amount": invoice_balance,
    #             "currency": "Fibb",
    #             "description": "test invoice generated by node2",
    #             "expiry": "0xe10",
    #             "final_cltv": "0x28",
    #             "payment_preimage": payment_preimage,
    #             "hash_algorithm": "sha256",
    #             "udt_type_script": {
    #                 "code_hash": self.udtContract.get_code_hash(True, self.node.rpcUrl),
    #                 "hash_type": "type",
    #                 "args": self.udtContract.get_owner_arg_by_lock_arg(self.account1["lock_arg"]),
    #             },
    #         }
    #     )
    #     before_channel = self.fiber1.get_client().list_channels({})
    #
    #     self.fiber1.get_client().send_payment(
    #         {
    #             "invoice": invoice["invoice_address"],
    #         }
    #     )
    #     time.sleep(10)
    #     after_channel = self.fiber1.get_client().list_channels({})
    #     assert (
    #             int(before_channel["channels"][0]["local_balance"], 16)
    #             - int(after_channel["channels"][0]["local_balance"], 16)
    #             == int(invoice_balance, 16)
    #     )
    #
    #     invoice_balance = hex(160 * 100000000)
    #     payment_preimage = generate_random_preimage()
    #     invoice = self.fiber1.get_client().new_invoice(
    #         {
    #             "amount": invoice_balance,
    #             "currency": "Fibb",
    #             "description": "test invoice generated by node2",
    #             "expiry": "0xe10",
    #             "final_cltv": "0x28",
    #             "payment_preimage": payment_preimage,
    #             "hash_algorithm": "sha256",
    #             "udt_type_script": {
    #                 "code_hash": self.udtContract.get_code_hash(True, self.node.rpcUrl),
    #                 "hash_type": "type",
    #                 "args": self.udtContract.get_owner_arg_by_lock_arg(self.account1["lock_arg"]),
    #             },
    #         }
    #     )
    #     before_channel = self.fiber2.get_client().list_channels({})
    #     print("node2 send 1 ckb failed ")
    #     with pytest.raises(Exception) as exc_info:
    #         self.fiber2.get_client().send_payment(
    #             {
    #                 "invoice": invoice["invoice_address"],
    #             }
    #         )
    #     expected_error_message = (
    #         "no path found"
    #     )
    #     assert expected_error_message in exc_info.value.args[0], (
    #         f"Expected substring '{expected_error_message}' "
    #         f"not found in actual string '{exc_info.value.args[0]}'"
    #     )
    #
    #     channels = self.fiber1.get_client().list_channels(
    #         {"peer_id": self.fiber2.get_peer_id()}
    #     )
    #     N1N2_CHANNEL_ID = channels["channels"][0]["channel_id"]
    #     self.fiber1.get_client().graph_channels()
    #
    #     before_balance1 = self.Ckb_cli.wallet_get_capacity(
    #         self.account1["address"]["testnet"]
    #     )
    #     before_balance2 = self.Ckb_cli.wallet_get_capacity(
    #         self.account2["address"]["testnet"]
    #     )
    #     # shut down
    #     self.fiber1.get_client().shutdown_channel(
    #         {
    #             "channel_id": N1N2_CHANNEL_ID,
    #             "close_script": {
    #                 "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
    #                 "hash_type": "type",
    #                 "args": self.account1["lock_arg"],
    #             },
    #             "fee_rate": "0x3FC",
    #         }
    #     )
    #     # todo wait close tx commit
    #     time.sleep(20)
    #     after_balance1 = self.Ckb_cli.wallet_get_capacity(self.account1["address"]["testnet"])
    #     after_balance2 = self.Ckb_cli.wallet_get_capacity(
    #         self.account2["address"]["testnet"]
    #     )
    #     print("before_balance1:", before_balance1)
    #     print("before_balance2:", before_balance2)
    #     print("after_balance1:", after_balance1)
    #     print("after_balance2:", after_balance2)

    # def test_tlc_max_value_none(self):
    #     """
    #     tlc_max_value: none
    #     Returns:
    #     """
    #
    # def test_ckb_tlc_max_value_not_eq_default(self):
    #     """
    #     tlc_max_value != default
    #     Returns:
    #
    #     """
    #
    # def test_udt_tlc_max_value_not_eq_default(self):
    #     """
    #     tlc_max_value != default
    #     Returns:
    #
    #     """
    #     self.fiber1.connect_peer(self.fiber2)
    #     time.sleep(5)
    #     self.fiber1.get_client().open_channel(
    #         {
    #             "peer_id": self.fiber2.get_peer_id(),
    #             "funding_amount": hex(1000 * 100000000),
    #             "public": True,
    #             "tlc_max_value": hex(160 * 100000000 - 1),
    #             "funding_udt_type_script": {
    #                 "code_hash": self.udtContract.get_code_hash(True, self.node.rpcUrl),
    #                 "hash_type": "type",
    #                 "args": self.udtContract.get_owner_arg_by_lock_arg(self.account1["lock_arg"]),
    #             },
    #             # "tlc_fee_proportional_millionths": "0x4B0",
    #         }
    #     )
    #
    #     time.sleep(1)
    #     wait_for_channel_state(
    #         self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
    #     )
    #     time.sleep(5)
    #     # transfer
    #     self.fiber1.get_client().graph_channels()
    #     self.fiber1.get_client().graph_nodes()
    #     payment_preimage = generate_random_preimage()
    #     channels = self.fiber1.get_client().list_channels({})
    #     invoice_balance = hex(500 * 100000000)
    #
    #     invoice = self.fiber2.get_client().new_invoice(
    #         {
    #             "amount": invoice_balance,
    #             "currency": "Fibb",
    #             "description": "test invoice generated by node2",
    #             "expiry": "0xe10",
    #             "final_cltv": "0x28",
    #             "payment_preimage": payment_preimage,
    #             "hash_algorithm": "sha256",
    #             "udt_type_script": {
    #                 "code_hash": self.udtContract.get_code_hash(True, self.node.rpcUrl),
    #                 "hash_type": "type",
    #                 "args": self.udtContract.get_owner_arg_by_lock_arg(self.account1["lock_arg"]),
    #             },
    #         }
    #     )
    #     before_channel = self.fiber1.get_client().list_channels({})
    #
    #     self.fiber1.get_client().send_payment(
    #         {
    #             "invoice": invoice["invoice_address"],
    #         }
    #     )
    #     time.sleep(10)
    #     after_channel = self.fiber1.get_client().list_channels({})
    #     assert (
    #             int(before_channel["channels"][0]["local_balance"], 16)
    #             - int(after_channel["channels"][0]["local_balance"], 16)
    #             == int(invoice_balance, 16)
    #     )
    #
    #     invoice_balance = hex(160 * 100000000)
    #     payment_preimage = generate_random_preimage()
    #     invoice = self.fiber1.get_client().new_invoice(
    #         {
    #             "amount": invoice_balance,
    #             "currency": "Fibb",
    #             "description": "test invoice generated by node2",
    #             "expiry": "0xe10",
    #             "final_cltv": "0x28",
    #             "payment_preimage": payment_preimage,
    #             "hash_algorithm": "sha256",
    #             "udt_type_script": {
    #                 "code_hash": self.udtContract.get_code_hash(True, self.node.rpcUrl),
    #                 "hash_type": "type",
    #                 "args": self.udtContract.get_owner_arg_by_lock_arg(self.account1["lock_arg"]),
    #             },
    #         }
    #     )
    #     before_channel = self.fiber2.get_client().list_channels({})
    #     print("node2 send 1 ckb failed ")
    #     with pytest.raises(Exception) as exc_info:
    #         self.fiber2.get_client().send_payment(
    #             {
    #                 "invoice": invoice["invoice_address"],
    #             }
    #         )
    #     expected_error_message = (
    #         "no path found"
    #     )
    #     assert expected_error_message in exc_info.value.args[0], (
    #         f"Expected substring '{expected_error_message}' "
    #         f"not found in actual string '{exc_info.value.args[0]}'"
    #     )
    #
    #     channels = self.fiber1.get_client().list_channels(
    #         {"peer_id": self.fiber2.get_peer_id()}
    #     )
    #     N1N2_CHANNEL_ID = channels["channels"][0]["channel_id"]
    #     self.fiber1.get_client().graph_channels()
    #
    #     before_balance1 = self.Ckb_cli.wallet_get_capacity(
    #         self.account1["address"]["testnet"]
    #     )
    #     before_balance2 = self.Ckb_cli.wallet_get_capacity(
    #         self.account2["address"]["testnet"]
    #     )
    #     # shut down
    #     self.fiber1.get_client().shutdown_channel(
    #         {
    #             "channel_id": N1N2_CHANNEL_ID,
    #             "close_script": {
    #                 "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
    #                 "hash_type": "type",
    #                 "args": self.account1["lock_arg"],
    #             },
    #             "fee_rate": "0x3FC",
    #         }
    #     )
    #     # todo wait close tx commit
    #     time.sleep(20)
    #     after_balance1 = self.Ckb_cli.wallet_get_capacity(self.account1["address"]["testnet"])
    #     after_balance2 = self.Ckb_cli.wallet_get_capacity(
    #         self.account2["address"]["testnet"]
    #     )
    #     print("before_balance1:", before_balance1)
    #     print("before_balance2:", before_balance2)
    #     print("after_balance1:", after_balance1)
    #     print("after_balance2:", after_balance2)

    # def test_tlc_fee_proportional_millionths_default(self):
    #     """
    #
    #     tlc_fee_proportional_millionths : none
    #     Returns:
    #     """
    #     account3_private_key = "0x200c06bfd800d27397002dca6fb0993d5ba6399b4238b2f29ee9deb97593d2b1"
    #     account3 = self.Ckb_cli.util_key_info_by_private_key(account3_private_key)
    #     tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(self.Config.ACCOUNT_PRIVATE_1,
    #                                                           account3["address"]["testnet"],
    #                                                           1000,
    #                                                           self.node.rpcUrl)
    #     self.Miner.miner_until_tx_committed(self.node, tx_hash)
    #     tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(self.Config.ACCOUNT_PRIVATE_1,
    #                                                           account3["address"]["testnet"],
    #                                                           1000,
    #                                                           self.node.rpcUrl)
    #     self.Miner.miner_until_tx_committed(self.node, tx_hash)
    #
    #     # start fiber3
    #     self.fiber3 = Fiber.init_by_port(
    #         FiberConfigPath.V100_DEV,
    #         account3_private_key,
    #         "fiber/node3",
    #         "8231",
    #         "8232",
    #     )
    #     self.fibers.append(self.fiber3)
    #     deploy_hash, deploy_index = self.udtContract.get_deploy_hash_and_index()
    #
    #     self.fiber3.prepare(
    #         update_config={
    #             "ckb_rpc_url": self.node.rpcUrl,
    #             "ckb_udt_whitelist": True,
    #             "xudt_script_code_hash": self.Contract.get_ckb_contract_codehash(
    #                 deploy_hash, deploy_index, True, self.node.rpcUrl
    #             ),
    #             "xudt_cell_deps_tx_hash": deploy_hash,
    #             "xudt_cell_deps_index": deploy_index,
    #         }
    #     )
    #     self.fiber3.start(self.node)
    #     # self.fiber3.connect_peer(self.fiber2)
    #     time.sleep(3)
    #     self.fiber2.connect_peer(self.fiber3)
    #     time.sleep(3)
    #     temporary_channel_id = self.fiber1.get_client().open_channel(
    #         {
    #             "peer_id": self.fiber2.get_peer_id(),
    #             "funding_amount": hex(200 * 100000000),
    #             "public": True,
    #             # "funding_fee_rate": "0xffff",
    #             # "tlc_fee_proportional_millionths": "0x4B0",
    #
    #         }
    #     )
    #     time.sleep(1)
    #     wait_for_channel_state(
    #         self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
    #     )
    #     temporary_channel_id = self.fiber2.get_client().open_channel(
    #         {
    #             "peer_id": self.fiber3.get_peer_id(),
    #             "funding_amount": hex(1000 * 100000000),
    #             "public": True,
    #             # "tlc_min_value": hex(2 * 100000000)
    #             # "funding_fee_rate": "0xffff",
    #             # "tlc_fee_proportional_millionths": "0x4B0",
    #
    #         }
    #     )
    #     time.sleep(1)
    #     wait_for_channel_state(
    #         self.fiber2.get_client(), self.fiber3.get_peer_id(), "CHANNEL_READY", 120
    #     )
    #     invoice_balance = hex(100 * 100000000)
    #     payment_preimage = generate_random_preimage()
    #     invoice = self.fiber3.get_client().new_invoice(
    #         {
    #             "amount": invoice_balance,
    #             "currency": "Fibb",
    #             "description": "test invoice generated by node2",
    #             "expiry": "0xe10",
    #             "final_cltv": "0x28",
    #             "payment_preimage": payment_preimage,
    #             "hash_algorithm": "sha256",
    #         })
    #     before_channel_12 = self.fiber1.get_client().list_channels({})
    #     before_channel_32 = self.fiber3.get_client().list_channels({})
    #     time.sleep(10)
    #     self.fiber2.get_client().graph_channels()
    #     self.fiber2.get_client().graph_nodes()
    #     self.fiber1.get_client().send_payment(
    #         {
    #             "invoice": invoice["invoice_address"],
    #         }
    #     )
    #     time.sleep(10)
    #     after_channel_12 = self.fiber1.get_client().list_channels({})
    #     after_channel_32 = self.fiber3.get_client().list_channels({})
    #
    #     print("before_channel_12:", before_channel_12)
    #     print("before_channel_32:", before_channel_32)
    #     print("after_channel_12:", after_channel_12)
    #     print("after_channel_32:", after_channel_32)
    #
    #     assert (
    #             int(before_channel_12["channels"][0]["local_balance"], 16)
    #             - int(after_channel_12["channels"][0]["local_balance"], 16)
    #             == (int(invoice_balance, 16) + int(int(invoice_balance, 16) * 0.001))
    #     )
    #
    #     assert (
    #             int(after_channel_32["channels"][0]["local_balance"], 16)
    #             - int(before_channel_32["channels"][0]["local_balance"], 16)
    #             == int(invoice_balance, 16)
    #     )
    #
    # def test_tlc_fee_proportional_millionths_overflow(self):
    #     """
    #     tlc_fee_proportional_millionths > int.max
    #     Returns:
    #     """
    #     with pytest.raises(Exception) as exc_info:
    #         temporary_channel_id = self.fiber2.get_client().open_channel(
    #             {
    #                 "peer_id": self.fiber1.get_peer_id(),
    #                 "funding_amount": hex(1000 * 100000000),
    #                 "public": True,
    #                 # "tlc_min_value": hex(2 * 100000000)
    #                 # "funding_fee_rate": "0xffff",
    #                 "tlc_fee_proportional_millionths": "0x1FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF",
    #
    #             }
    #         )
    #     expected_error_message = (
    #         "Invalid params"
    #     )
    #     assert expected_error_message in exc_info.value.args[0], (
    #         f"Expected substring '{expected_error_message}' "
    #         f"not found in actual string '{exc_info.value.args[0]}'"
    #     )
    #
    # def test_ckb_tlc_fee_proportional_millionths_not_eq_default(self):
    #     """
    #     tlc_fee_proportional_millionths != default
    #     Returns:
    #     """
    #     account3_private_key = "0x200c06bfd800d27397002dca6fb0993d5ba6399b4238b2f29ee9deb97593d2b1"
    #     account3 = self.Ckb_cli.util_key_info_by_private_key(account3_private_key)
    #     tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(self.Config.ACCOUNT_PRIVATE_1,
    #                                                           account3["address"]["testnet"],
    #                                                           1000,
    #                                                           self.node.rpcUrl)
    #     self.Miner.miner_until_tx_committed(self.node, tx_hash)
    #     tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(self.Config.ACCOUNT_PRIVATE_1,
    #                                                           account3["address"]["testnet"],
    #                                                           1000,
    #                                                           self.node.rpcUrl)
    #     self.Miner.miner_until_tx_committed(self.node, tx_hash)
    #
    #     # start fiber3
    #     self.fiber3 = Fiber.init_by_port(
    #         FiberConfigPath.V100_DEV,
    #         account3_private_key,
    #         "fiber/node3",
    #         "8231",
    #         "8232",
    #     )
    #     self.fibers.append(self.fiber3)
    #     deploy_hash, deploy_index = self.udtContract.get_deploy_hash_and_index()
    #
    #     self.fiber3.prepare(
    #         update_config={
    #             "ckb_rpc_url": self.node.rpcUrl,
    #             "ckb_udt_whitelist": True,
    #             "xudt_script_code_hash": self.Contract.get_ckb_contract_codehash(
    #                 deploy_hash, deploy_index, True, self.node.rpcUrl
    #             ),
    #             "xudt_cell_deps_tx_hash": deploy_hash,
    #             "xudt_cell_deps_index": deploy_index,
    #         }
    #     )
    #     self.fiber3.start(self.node)
    #     # self.fiber3.connect_peer(self.fiber2)
    #     time.sleep(3)
    #     self.fiber2.connect_peer(self.fiber3)
    #     time.sleep(3)
    #     temporary_channel_id = self.fiber1.get_client().open_channel(
    #         {
    #             "peer_id": self.fiber2.get_peer_id(),
    #             "funding_amount": hex(200 * 100000000),
    #             "public": True,
    #             # "funding_fee_rate": "0xffff",
    #             "tlc_fee_proportional_millionths": hex(1000000),
    #
    #         }
    #     )
    #     time.sleep(1)
    #     wait_for_channel_state(
    #         self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
    #     )
    #     fiber2_tlc_fee = 1000000
    #     temporary_channel_id = self.fiber2.get_client().open_channel(
    #         {
    #             "peer_id": self.fiber3.get_peer_id(),
    #             "funding_amount": hex(1000 * 100000000),
    #             "public": True,
    #             "tlc_fee_proportional_millionths": hex(fiber2_tlc_fee),
    #             # "tlc_min_value": hex(2 * 100000000)
    #             # "funding_fee_rate": "0xffff",
    #             # "tlc_fee_proportional_millionths": "0x4B0",
    #
    #         }
    #     )
    #     time.sleep(1)
    #     wait_for_channel_state(
    #         self.fiber2.get_client(), self.fiber3.get_peer_id(), "CHANNEL_READY", 120
    #     )
    #     invoice_balance = hex(100 * 100000000)
    #     payment_preimage = generate_random_preimage()
    #     invoice = self.fiber3.get_client().new_invoice(
    #         {
    #             "amount": invoice_balance,
    #             "currency": "Fibb",
    #             "description": "test invoice generated by node2",
    #             "expiry": "0xe10",
    #             "final_cltv": "0x28",
    #             "payment_preimage": payment_preimage,
    #             "hash_algorithm": "sha256",
    #         })
    #     before_channel_12 = self.fiber1.get_client().list_channels({})
    #     before_channel_32 = self.fiber3.get_client().list_channels({})
    #     time.sleep(10)
    #     self.fiber2.get_client().graph_channels()
    #     self.fiber2.get_client().graph_nodes()
    #     self.fiber1.get_client().send_payment(
    #         {
    #             "invoice": invoice["invoice_address"],
    #         }
    #     )
    #     time.sleep(10)
    #     after_channel_12 = self.fiber1.get_client().list_channels({})
    #     after_channel_32 = self.fiber3.get_client().list_channels({})
    #
    #     print("before_channel_12:", before_channel_12)
    #     print("before_channel_32:", before_channel_32)
    #     print("after_channel_12:", after_channel_12)
    #     print("after_channel_32:", after_channel_32)
    #
    #     assert (
    #             int(before_channel_12["channels"][0]["local_balance"], 16)
    #             - int(after_channel_12["channels"][0]["local_balance"], 16)
    #             == (int(invoice_balance, 16) + int(int(invoice_balance, 16) * 0.001))
    #     )
    #
    #     assert (
    #             int(after_channel_32["channels"][0]["local_balance"], 16)
    #             - int(before_channel_32["channels"][0]["local_balance"], 16)
    #             == int(invoice_balance, 16)
    #     )
    #     invoice_balance = hex(1 * 1000000)
    #     invoice = self.fiber1.get_client().new_invoice(
    #         {
    #             "amount": invoice_balance,
    #             "currency": "Fibb",
    #             "description": "test invoice generated by node2",
    #             "expiry": "0xe10",
    #             "final_cltv": "0x28",
    #             "payment_preimage": payment_preimage,
    #             "hash_algorithm": "sha256",
    #         })
    #     time.sleep(1)
    #     payment = self.fiber3.get_client().send_payment({
    #         "invoice": invoice["invoice_address"],
    #         "max_fee_amount": hex(1000 * 100000000)
    #     })
    #     time.sleep(5)
    #     self.fiber3.get_client().get_payment({"payment_hash": payment['payment_hash']})
    #     after_channel_2_12 = self.fiber1.get_client().list_channels({})
    #     after_channel_2_32 = self.fiber3.get_client().list_channels({})
    #     self.fiber3.get_client().graph_nodes()
    #     print("after_channel_2_12:", after_channel_2_12)
    #     print("after_channel_2_12:", after_channel_2_32)
    #     # assert
    #     assert (
    #             int(after_channel_32["channels"][0]["local_balance"], 16)
    #             - int(after_channel_2_32["channels"][0]["local_balance"], 16)
    #             == int(invoice_balance, 16) + int(invoice_balance, 16) * fiber2_tlc_fee / 1000000
    #     )
    #
    #     assert (
    #             int(after_channel_2_12["channels"][0]["local_balance"], 16)
    #             - int(after_channel_12["channels"][0]["local_balance"], 16)
    #             == int(invoice_balance, 16)
    #     )
    #
    # def test_udt_tlc_fee_proportional_millionths_not_eq_default(self):
    #     """
    #     tlc_fee_proportional_millionths != default
    #     Returns:
    #     """
    #     account3_private_key = "0x200c06bfd800d27397002dca6fb0993d5ba6399b4238b2f29ee9deb97593d2b1"
    #     account3 = self.Ckb_cli.util_key_info_by_private_key(account3_private_key)
    #     tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(self.Config.ACCOUNT_PRIVATE_1,
    #                                                           account3["address"]["testnet"],
    #                                                           1000,
    #                                                           self.node.rpcUrl)
    #     self.Miner.miner_until_tx_committed(self.node, tx_hash)
    #     tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(self.Config.ACCOUNT_PRIVATE_2,
    #                                                           self.account1["address"]["testnet"],
    #                                                           10000,
    #                                                           self.node.rpcUrl)
    #     self.Miner.miner_until_tx_committed(self.node, tx_hash)
    #
    #     tx_hash = issue_udt_tx(self.udtContract, self.node.rpcUrl, self.Config.ACCOUNT_PRIVATE_1,
    #                            self.Config.ACCOUNT_PRIVATE_2, 1000 * 100000000)
    #     self.Miner.miner_until_tx_committed(self.node, tx_hash)
    #     account1_cells = self.udtContract.list_cell(self.node.getClient(), self.account1['lock_arg'],
    #                                                 self.account1['lock_arg'])
    #     account2_cells = self.udtContract.list_cell(self.node.getClient(), self.account1['lock_arg'],
    #                                                 self.account2['lock_arg'])
    #     print("account1:", account1_cells)
    #     print("account2:", account2_cells)
    #     tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(self.Config.ACCOUNT_PRIVATE_2,
    #                                                           self.account1["address"]["testnet"],
    #                                                           10000,
    #                                                           self.node.rpcUrl)
    #     self.Miner.miner_until_tx_committed(self.node, tx_hash)
    #
    #     # start fiber3
    #     self.fiber3 = Fiber.init_by_port(
    #         FiberConfigPath.V100_DEV,
    #         account3_private_key,
    #         "fiber/node3",
    #         "8231",
    #         "8232",
    #     )
    #     self.fibers.append(self.fiber3)
    #     deploy_hash, deploy_index = self.udtContract.get_deploy_hash_and_index()
    #
    #     self.fiber3.prepare(
    #         update_config={
    #             "ckb_rpc_url": self.node.rpcUrl,
    #             "ckb_udt_whitelist": True,
    #             "xudt_script_code_hash": self.Contract.get_ckb_contract_codehash(
    #                 deploy_hash, deploy_index, True, self.node.rpcUrl
    #             ),
    #             "xudt_cell_deps_tx_hash": deploy_hash,
    #             "xudt_cell_deps_index": deploy_index,
    #         }
    #     )
    #     self.fiber3.start(self.node)
    #     # self.fiber3.connect_peer(self.fiber2)
    #     time.sleep(3)
    #     self.fiber2.connect_peer(self.fiber3)
    #     time.sleep(3)
    #     temporary_channel_id = self.fiber1.get_client().open_channel(
    #         {
    #             "peer_id": self.fiber2.get_peer_id(),
    #             "funding_amount": hex(200 * 100000000),
    #             "public": True,
    #             # "funding_fee_rate": "0xffff",
    #             "tlc_fee_proportional_millionths": hex(1000000),
    #             "funding_udt_type_script": {
    #                 "code_hash": self.udtContract.get_code_hash(True, self.node.rpcUrl),
    #                 "hash_type": "type",
    #                 "args": self.udtContract.get_owner_arg_by_lock_arg(self.account1["lock_arg"]),
    #             },
    #         }
    #     )
    #     time.sleep(1)
    #     wait_for_channel_state(
    #         self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
    #     )
    #     fiber2_tlc_fee = 1000000
    #     temporary_channel_id = self.fiber2.get_client().open_channel(
    #         {
    #             "peer_id": self.fiber3.get_peer_id(),
    #             "funding_amount": hex(1000 * 100000000),
    #             "public": True,
    #             "tlc_fee_proportional_millionths": hex(fiber2_tlc_fee),
    #             "funding_udt_type_script": {
    #                 "code_hash": self.udtContract.get_code_hash(True, self.node.rpcUrl),
    #                 "hash_type": "type",
    #                 "args": self.udtContract.get_owner_arg_by_lock_arg(self.account1["lock_arg"]),
    #             },
    #             # "tlc_min_value": hex(2 * 100000000)
    #             # "funding_fee_rate": "0xffff",
    #             # "tlc_fee_proportional_millionths": "0x4B0",
    #
    #         }
    #     )
    #     time.sleep(1)
    #     wait_for_channel_state(
    #         self.fiber2.get_client(), self.fiber3.get_peer_id(), "CHANNEL_READY", 120
    #     )
    #     invoice_balance = hex(100 * 100000000)
    #     payment_preimage = generate_random_preimage()
    #     invoice = self.fiber3.get_client().new_invoice(
    #         {
    #             "amount": invoice_balance,
    #             "currency": "Fibb",
    #             "description": "test invoice generated by node2",
    #             "expiry": "0xe10",
    #             "final_cltv": "0x28",
    #             "payment_preimage": payment_preimage,
    #             "hash_algorithm": "sha256",
    #             "udt_type_script": {
    #                 "code_hash": self.udtContract.get_code_hash(True, self.node.rpcUrl),
    #                 "hash_type": "type",
    #                 "args": self.udtContract.get_owner_arg_by_lock_arg(self.account1["lock_arg"]),
    #             },
    #         })
    #     before_channel_12 = self.fiber1.get_client().list_channels({})
    #     before_channel_32 = self.fiber3.get_client().list_channels({})
    #     time.sleep(10)
    #     self.fiber2.get_client().graph_channels()
    #     self.fiber2.get_client().graph_nodes()
    #     self.fiber1.get_client().send_payment(
    #         {
    #             "invoice": invoice["invoice_address"],
    #         }
    #     )
    #     time.sleep(10)
    #     after_channel_12 = self.fiber1.get_client().list_channels({})
    #     after_channel_32 = self.fiber3.get_client().list_channels({})
    #
    #     print("before_channel_12:", before_channel_12)
    #     print("before_channel_32:", before_channel_32)
    #     print("after_channel_12:", after_channel_12)
    #     print("after_channel_32:", after_channel_32)
    #
    #     assert (
    #             int(before_channel_12["channels"][0]["local_balance"], 16)
    #             - int(after_channel_12["channels"][0]["local_balance"], 16)
    #             == (int(invoice_balance, 16) + int(int(invoice_balance, 16) * 0.001))
    #     )
    #
    #     assert (
    #             int(after_channel_32["channels"][0]["local_balance"], 16)
    #             - int(before_channel_32["channels"][0]["local_balance"], 16)
    #             == int(invoice_balance, 16)
    #     )
    #     invoice_balance = hex(1 * 100000000)
    #     invoice = self.fiber1.get_client().new_invoice(
    #         {
    #             "amount": invoice_balance,
    #             "currency": "Fibb",
    #             "description": "test invoice generated by node2",
    #             "expiry": "0xe10",
    #             "final_cltv": "0x28",
    #             "payment_preimage": payment_preimage,
    #             "hash_algorithm": "sha256",
    #             "udt_type_script": {
    #                 "code_hash": self.udtContract.get_code_hash(True, self.node.rpcUrl),
    #                 "hash_type": "type",
    #                 "args": self.udtContract.get_owner_arg_by_lock_arg(self.account1["lock_arg"]),
    #             },
    #         })
    #     time.sleep(1)
    #     payment = self.fiber3.get_client().send_payment({
    #         "invoice": invoice["invoice_address"],
    #         "max_fee_amount": hex(1000 * 100000000)
    #     })
    #     time.sleep(5)
    #     self.fiber3.get_client().get_payment({"payment_hash": payment['payment_hash']})
    #     after_channel_2_12 = self.fiber1.get_client().list_channels({})
    #     after_channel_2_32 = self.fiber3.get_client().list_channels({})
    #     self.fiber3.get_client().graph_nodes()
    #     print("after_channel_2_12:", after_channel_2_12)
    #     print("after_channel_2_12:", after_channel_2_32)
    #     # assert
    #     assert (
    #             int(after_channel_32["channels"][0]["local_balance"], 16)
    #             - int(after_channel_2_32["channels"][0]["local_balance"], 16)
    #             == int(invoice_balance, 16) + int(invoice_balance, 16) * fiber2_tlc_fee / 1000000
    #     )
    #
    #     assert (
    #             int(after_channel_2_12["channels"][0]["local_balance"], 16)
    #             - int(after_channel_12["channels"][0]["local_balance"], 16)
    #             == int(invoice_balance, 16)
    #     )
    #
    # def test_max_tlc_value_in_flight_none(self):
    #     """
    #     max_tlc_value_in_flight = none
    #     Returns:
    #     """
    #     self.test_linked_peer()
    #
    # def test_max_tlc_value_in_flight_is_zero(self):
    #     """
    #     max_tlc_value_in_flight = 0
    #     Returns:
    #     """
    #     self.fiber1.connect_peer(self.fiber2)
    #     time.sleep(5)
    #     self.fiber1.get_client().open_channel(
    #         {
    #             "peer_id": self.fiber2.get_peer_id(),
    #             "funding_amount": hex(1000 * 100000000),
    #             "public": True,
    #             "max_tlc_value_in_flight": "0x0",
    #             "funding_udt_type_script": {
    #                 "code_hash": self.udtContract.get_code_hash(True, self.node.rpcUrl),
    #                 "hash_type": "type",
    #                 "args": self.udtContract.get_owner_arg_by_lock_arg(self.account1["lock_arg"]),
    #             },
    #             # "tlc_fee_proportional_millionths": "0x4B0",
    #         }
    #     )
    #
    #     time.sleep(1)
    #     wait_for_channel_state(
    #         self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
    #     )
    #     time.sleep(5)
    #     # transfer
    #     self.fiber1.get_client().graph_channels()
    #     self.fiber1.get_client().graph_nodes()
    #     payment_preimage = generate_random_preimage()
    #     channels = self.fiber1.get_client().list_channels({})
    #     invoice_balance = hex(500 * 100000000)
    #
    #     invoice = self.fiber2.get_client().new_invoice(
    #         {
    #             "amount": invoice_balance,
    #             "currency": "Fibb",
    #             "description": "test invoice generated by node2",
    #             "expiry": "0xe10",
    #             "final_cltv": "0x28",
    #             "payment_preimage": payment_preimage,
    #             "hash_algorithm": "sha256",
    #             "udt_type_script": {
    #                 "code_hash": self.udtContract.get_code_hash(True, self.node.rpcUrl),
    #                 "hash_type": "type",
    #                 "args": self.udtContract.get_owner_arg_by_lock_arg(self.account1["lock_arg"]),
    #             },
    #         }
    #     )
    #     before_channel = self.fiber1.get_client().list_channels({})
    #
    #     self.fiber1.get_client().send_payment(
    #         {
    #             "invoice": invoice["invoice_address"],
    #         }
    #     )
    #     time.sleep(10)
    #     after_channel = self.fiber1.get_client().list_channels({})
    #     assert (
    #             int(before_channel["channels"][0]["local_balance"], 16)
    #             - int(after_channel["channels"][0]["local_balance"], 16)
    #             == int(invoice_balance, 16)
    #     )
    #
    #     invoice_balance = hex(160 * 100000000)
    #     payment_preimage = generate_random_preimage()
    #     invoice = self.fiber1.get_client().new_invoice(
    #         {
    #             "amount": invoice_balance,
    #             "currency": "Fibb",
    #             "description": "test invoice generated by node2",
    #             "expiry": "0xe10",
    #             "final_cltv": "0x28",
    #             "payment_preimage": payment_preimage,
    #             "hash_algorithm": "sha256",
    #             "udt_type_script": {
    #                 "code_hash": self.udtContract.get_code_hash(True, self.node.rpcUrl),
    #                 "hash_type": "type",
    #                 "args": self.udtContract.get_owner_arg_by_lock_arg(self.account1["lock_arg"]),
    #             },
    #         }
    #     )
    #     before_channel = self.fiber2.get_client().list_channels({})
    #     print("node2 send 1 ckb failed ")
    #     with pytest.raises(Exception) as exc_info:
    #         self.fiber2.get_client().send_payment(
    #             {
    #                 "invoice": invoice["invoice_address"],
    #             }
    #         )
    #     expected_error_message = (
    #         "no path found"
    #     )
    #     assert expected_error_message in exc_info.value.args[0], (
    #         f"Expected substring '{expected_error_message}' "
    #         f"not found in actual string '{exc_info.value.args[0]}'"
    #     )
    #
    #     channels = self.fiber1.get_client().list_channels(
    #         {"peer_id": self.fiber2.get_peer_id()}
    #     )
    #     N1N2_CHANNEL_ID = channels["channels"][0]["channel_id"]
    #     self.fiber1.get_client().graph_channels()
    #
    #     before_balance1 = self.Ckb_cli.wallet_get_capacity(
    #         self.account1["address"]["testnet"]
    #     )
    #     before_balance2 = self.Ckb_cli.wallet_get_capacity(
    #         self.account2["address"]["testnet"]
    #     )
    #     # shut down
    #     self.fiber1.get_client().shutdown_channel(
    #         {
    #             "channel_id": N1N2_CHANNEL_ID,
    #             "close_script": {
    #                 "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
    #                 "hash_type": "type",
    #                 "args": self.account1["lock_arg"],
    #             },
    #             "fee_rate": "0x3FC",
    #         }
    #     )
    #     # todo wait close tx commit
    #     time.sleep(20)
    #     after_balance1 = self.Ckb_cli.wallet_get_capacity(self.account1["address"]["testnet"])
    #     after_balance2 = self.Ckb_cli.wallet_get_capacity(
    #         self.account2["address"]["testnet"]
    #     )
    #     print("before_balance1:", before_balance1)
    #     print("before_balance2:", before_balance2)
    #     print("after_balance1:", after_balance1)
    #     print("after_balance2:", after_balance2)
    #
    # def test_max_tlc_value_in_flight_overflow(self):
    #     with pytest.raises(Exception) as exc_info:
    #         temporary_channel_id = self.fiber2.get_client().open_channel(
    #             {
    #                 "peer_id": self.fiber1.get_peer_id(),
    #                 "funding_amount": hex(1000 * 100000000),
    #                 "public": True,
    #                 # "tlc_min_value": hex(2 * 100000000)
    #                 # "funding_fee_rate": "0xffff",
    #                 "max_tlc_value_in_flight": "0x1FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF",
    #
    #             }
    #         )
    #     expected_error_message = (
    #         "Invalid params"
    #     )
    #     assert expected_error_message in exc_info.value.args[0], (
    #         f"Expected substring '{expected_error_message}' "
    #         f"not found in actual string '{exc_info.value.args[0]}'"
    #     )
    #
    # def test_ckb_max_tlc_value_in_flight_too_min(self):
    #     """
    #     max_tlc_value_in_flight == 1
    #     Returns:
    #     """
    #     self.fiber1.connect_peer(self.fiber2)
    #     time.sleep(5)
    #     self.fiber1.get_client().open_channel(
    #         {
    #             "peer_id": self.fiber2.get_peer_id(),
    #             "funding_amount": hex(1000 * 100000000),
    #             "public": True,
    #             "max_tlc_value_in_flight": "0x1",
    #
    #             # "tlc_fee_proportional_millionths": "0x4B0",
    #         }
    #     )
    #
    #     time.sleep(1)
    #     wait_for_channel_state(
    #         self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
    #     )
    #     time.sleep(5)
    #     # transfer
    #     self.fiber1.get_client().graph_channels()
    #     self.fiber1.get_client().graph_nodes()
    #     payment_preimage = generate_random_preimage()
    #     channels = self.fiber1.get_client().list_channels({})
    #     # send 0 ckb
    #     invoice_balance = hex(0)
    #
    #     invoice = self.fiber2.get_client().new_invoice(
    #         {
    #             "amount": invoice_balance,
    #             "currency": "Fibb",
    #             "description": "test invoice generated by node2",
    #             "expiry": "0xe10",
    #             "final_cltv": "0x28",
    #             "payment_preimage": payment_preimage,
    #             "hash_algorithm": "sha256",
    #         }
    #     )
    #     before_channel = self.fiber1.get_client().list_channels({})
    #
    #     with pytest.raises(Exception) as exc_info:
    #         self.fiber1.get_client().send_payment(
    #             {
    #                 "invoice": invoice["invoice_address"],
    #             }
    #         )
    #     expected_error_message = (
    #         "Failed to build route"
    #     )
    #     assert expected_error_message in exc_info.value.args[0], (
    #         f"Expected substring '{expected_error_message}' "
    #         f"not found in actual string '{exc_info.value.args[0]}'"
    #     )
    #     # send 0.00000001 ckb
    #     invoice_balance = hex(1)
    #     payment_preimage = generate_random_preimage()
    #
    #     invoice = self.fiber2.get_client().new_invoice(
    #         {
    #             "amount": invoice_balance,
    #             "currency": "Fibb",
    #             "description": "test invoice generated by node2",
    #             "expiry": "0xe10",
    #             "final_cltv": "0x28",
    #             "payment_preimage": payment_preimage,
    #             "hash_algorithm": "sha256",
    #         }
    #     )
    #     before_channel = self.fiber1.get_client().list_channels({})
    #
    #     self.fiber1.get_client().send_payment(
    #         {
    #             "invoice": invoice["invoice_address"],
    #         }
    #     )
    #     time.sleep(10)
    #     after_channel = self.fiber1.get_client().list_channels({})
    #     assert (
    #             int(before_channel["channels"][0]["local_balance"], 16)
    #             - int(after_channel["channels"][0]["local_balance"], 16)
    #             == int(invoice_balance, 16)
    #     )
    #
    #     invoice_balance = hex(1)
    #     payment_preimage = generate_random_preimage()
    #     invoice = self.fiber1.get_client().new_invoice(
    #         {
    #             "amount": invoice_balance,
    #             "currency": "Fibb",
    #             "description": "test invoice generated by node2",
    #             "expiry": "0xe10",
    #             "final_cltv": "0x28",
    #             "payment_preimage": payment_preimage,
    #             "hash_algorithm": "sha256",
    #         }
    #     )
    #     time.sleep(1)
    #     print("node2 send 1 ckb failed ")
    #     before_channel_2 = self.fiber2.get_client().list_channels({})
    #     self.fiber2.get_client().send_payment(
    #         {
    #             "invoice": invoice["invoice_address"],
    #         }
    #     )
    #     time.sleep(10)
    #     after_channel_2 = self.fiber2.get_client().list_channels({})
    #     assert (
    #             int(before_channel_2["channels"][0]["local_balance"], 16)
    #             - int(after_channel_2["channels"][0]["local_balance"], 16)
    #             == int(invoice_balance, 16)
    #     )
    #
    #     channels = self.fiber1.get_client().list_channels(
    #         {"peer_id": self.fiber2.get_peer_id()}
    #     )
    #     N1N2_CHANNEL_ID = channels["channels"][0]["channel_id"]
    #     self.fiber1.get_client().graph_channels()
    #
    #     before_balance1 = self.Ckb_cli.wallet_get_capacity(
    #         self.account1["address"]["testnet"]
    #     )
    #     before_balance2 = self.Ckb_cli.wallet_get_capacity(
    #         self.account2["address"]["testnet"]
    #     )
    #     # shut down
    #     self.fiber1.get_client().shutdown_channel(
    #         {
    #             "channel_id": N1N2_CHANNEL_ID,
    #             "close_script": {
    #                 "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
    #                 "hash_type": "type",
    #                 "args": self.account1["lock_arg"],
    #             },
    #             "fee_rate": "0x3FC",
    #         }
    #     )
    #     # todo wait close tx commit
    #     time.sleep(20)
    #     after_balance1 = self.Ckb_cli.wallet_get_capacity(self.account1["address"]["testnet"])
    #     after_balance2 = self.Ckb_cli.wallet_get_capacity(
    #         self.account2["address"]["testnet"]
    #     )
    #     print("before_balance1:", before_balance1)
    #     print("before_balance2:", before_balance2)
    #     print("after_balance1:", after_balance1)
    #     print("after_balance2:", after_balance2)
    #     assert after_balance2 - before_balance2 == 62
    #
    # def test_udt_max_tlc_value_in_flight_too_min(self):
    #     """
    #     max_tlc_value_in_flight == 1
    #     Returns:
    #     """
    #     self.fiber1.connect_peer(self.fiber2)
    #     time.sleep(5)
    #     self.fiber1.get_client().open_channel(
    #         {
    #             "peer_id": self.fiber2.get_peer_id(),
    #             "funding_amount": hex(1000 * 100000000),
    #             "public": True,
    #             "max_tlc_value_in_flight": "0x1",
    #             "funding_udt_type_script": {
    #                 "code_hash": self.udtContract.get_code_hash(True, self.node.rpcUrl),
    #                 "hash_type": "type",
    #                 "args": self.udtContract.get_owner_arg_by_lock_arg(self.account1["lock_arg"]),
    #             },
    #             # "tlc_fee_proportional_millionths": "0x4B0",
    #         }
    #     )
    #
    #     time.sleep(1)
    #     wait_for_channel_state(
    #         self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
    #     )
    #     time.sleep(5)
    #     # transfer
    #     self.fiber1.get_client().graph_channels()
    #     self.fiber1.get_client().graph_nodes()
    #     payment_preimage = generate_random_preimage()
    #     channels = self.fiber1.get_client().list_channels({})
    #     # send 0 ckb
    #     invoice_balance = hex(0)
    #
    #     invoice = self.fiber2.get_client().new_invoice(
    #         {
    #             "amount": invoice_balance,
    #             "currency": "Fibb",
    #             "description": "test invoice generated by node2",
    #             "expiry": "0xe10",
    #             "final_cltv": "0x28",
    #             "payment_preimage": payment_preimage,
    #             "hash_algorithm": "sha256",
    #             "udt_type_script": {
    #                 "code_hash": self.udtContract.get_code_hash(True, self.node.rpcUrl),
    #                 "hash_type": "type",
    #                 "args": self.udtContract.get_owner_arg_by_lock_arg(self.account1["lock_arg"]),
    #             },
    #         }
    #     )
    #     before_channel = self.fiber1.get_client().list_channels({})
    #
    #     with pytest.raises(Exception) as exc_info:
    #         self.fiber1.get_client().send_payment(
    #             {
    #                 "invoice": invoice["invoice_address"],
    #             }
    #         )
    #     expected_error_message = (
    #         "Failed to build route"
    #     )
    #     assert expected_error_message in exc_info.value.args[0], (
    #         f"Expected substring '{expected_error_message}' "
    #         f"not found in actual string '{exc_info.value.args[0]}'"
    #     )
    #     # send 0.00000001 ckb
    #     invoice_balance = hex(1)
    #     payment_preimage = generate_random_preimage()
    #
    #     invoice = self.fiber2.get_client().new_invoice(
    #         {
    #             "amount": invoice_balance,
    #             "currency": "Fibb",
    #             "description": "test invoice generated by node2",
    #             "expiry": "0xe10",
    #             "final_cltv": "0x28",
    #             "payment_preimage": payment_preimage,
    #             "hash_algorithm": "sha256",
    #             "udt_type_script": {
    #                 "code_hash": self.udtContract.get_code_hash(True, self.node.rpcUrl),
    #                 "hash_type": "type",
    #                 "args": self.udtContract.get_owner_arg_by_lock_arg(self.account1["lock_arg"]),
    #             },
    #         }
    #     )
    #     before_channel = self.fiber1.get_client().list_channels({})
    #
    #     self.fiber1.get_client().send_payment(
    #         {
    #             "invoice": invoice["invoice_address"],
    #         }
    #     )
    #     time.sleep(10)
    #     after_channel = self.fiber1.get_client().list_channels({})
    #     assert (
    #             int(before_channel["channels"][0]["local_balance"], 16)
    #             - int(after_channel["channels"][0]["local_balance"], 16)
    #             == int(invoice_balance, 16)
    #     )
    #
    #     invoice_balance = hex(1)
    #     payment_preimage = generate_random_preimage()
    #     invoice = self.fiber1.get_client().new_invoice(
    #         {
    #             "amount": invoice_balance,
    #             "currency": "Fibb",
    #             "description": "test invoice generated by node2",
    #             "expiry": "0xe10",
    #             "final_cltv": "0x28",
    #             "payment_preimage": payment_preimage,
    #             "hash_algorithm": "sha256",
    #             "udt_type_script": {
    #                 "code_hash": self.udtContract.get_code_hash(True, self.node.rpcUrl),
    #                 "hash_type": "type",
    #                 "args": self.udtContract.get_owner_arg_by_lock_arg(self.account1["lock_arg"]),
    #             },
    #         }
    #     )
    #     time.sleep(1)
    #     print("node2 send 1 ckb failed ")
    #     before_channel_2 = self.fiber2.get_client().list_channels({})
    #     self.fiber2.get_client().send_payment(
    #         {
    #             "invoice": invoice["invoice_address"],
    #         }
    #     )
    #     time.sleep(10)
    #     after_channel_2 = self.fiber2.get_client().list_channels({})
    #     assert (
    #             int(before_channel_2["channels"][0]["local_balance"], 16)
    #             - int(after_channel_2["channels"][0]["local_balance"], 16)
    #             == int(invoice_balance, 16)
    #     )
    #
    #     channels = self.fiber1.get_client().list_channels(
    #         {"peer_id": self.fiber2.get_peer_id()}
    #     )
    #     N1N2_CHANNEL_ID = channels["channels"][0]["channel_id"]
    #     self.fiber1.get_client().graph_channels()
    #
    #     before_balance1 = self.Ckb_cli.wallet_get_capacity(
    #         self.account1["address"]["testnet"]
    #     )
    #     before_balance2 = self.Ckb_cli.wallet_get_capacity(
    #         self.account2["address"]["testnet"]
    #     )
    #     # shut down
    #     self.fiber1.get_client().shutdown_channel(
    #         {
    #             "channel_id": N1N2_CHANNEL_ID,
    #             "close_script": {
    #                 "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
    #                 "hash_type": "type",
    #                 "args": self.account1["lock_arg"],
    #             },
    #             "fee_rate": "0x3FC",
    #         }
    #     )
    #     # todo wait close tx commit
    #     time.sleep(20)
    #     after_balance1 = self.Ckb_cli.wallet_get_capacity(self.account1["address"]["testnet"])
    #     after_balance2 = self.Ckb_cli.wallet_get_capacity(
    #         self.account2["address"]["testnet"]
    #     )
    #     print("before_balance1:", before_balance1)
    #     print("before_balance2:", before_balance2)
    #     print("after_balance1:", after_balance1)
    #     print("after_balance2:", after_balance2)
    #     assert after_balance2 - before_channel_2 == 143
    #
    # def test_ckb_max_tlc_value_in_flight_not_eq_default(self):
    #     """
    #     max_tlc_value_in_flight != default
    #     Returns:
    #
    #     """
    #     self.fiber1.connect_peer(self.fiber2)
    #     time.sleep(5)
    #     self.fiber1.get_client().open_channel(
    #         {
    #             "peer_id": self.fiber2.get_peer_id(),
    #             "funding_amount": hex(1000 * 100000000),
    #             "public": True,
    #             "max_tlc_value_in_flight": hex(1 * 100000000),
    #
    #             # "tlc_fee_proportional_millionths": "0x4B0",
    #         }
    #     )
    #
    #     time.sleep(1)
    #     wait_for_channel_state(
    #         self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
    #     )
    #     time.sleep(5)
    #     # transfer
    #     self.fiber1.get_client().graph_channels()
    #     self.fiber1.get_client().graph_nodes()
    #     payment_preimage = generate_random_preimage()
    #     channels = self.fiber1.get_client().list_channels({})
    #     # send 1.00000001 ckb
    #     invoice_balance = hex(1 * 100000000 + 1)
    #
    #     invoice = self.fiber2.get_client().new_invoice(
    #         {
    #             "amount": invoice_balance,
    #             "currency": "Fibb",
    #             "description": "test invoice generated by node2",
    #             "expiry": "0xe10",
    #             "final_cltv": "0x28",
    #             "payment_preimage": payment_preimage,
    #             "hash_algorithm": "sha256",
    #         }
    #     )
    #     before_channel = self.fiber1.get_client().list_channels({})
    #
    #     with pytest.raises(Exception) as exc_info:
    #         self.fiber1.get_client().send_payment(
    #             {
    #                 "invoice": invoice["invoice_address"],
    #             }
    #         )
    #     expected_error_message = (
    #         "TemporaryChannelFailure"
    #     )
    #     assert expected_error_message in exc_info.value.args[0], (
    #         f"Expected substring '{expected_error_message}' "
    #         f"not found in actual string '{exc_info.value.args[0]}'"
    #     )
    #     # send 1  ckb
    #     invoice_balance = hex(1 * 100000000)
    #     payment_preimage = generate_random_preimage()
    #
    #     invoice = self.fiber2.get_client().new_invoice(
    #         {
    #             "amount": invoice_balance,
    #             "currency": "Fibb",
    #             "description": "test invoice generated by node2",
    #             "expiry": "0xe10",
    #             "final_cltv": "0x28",
    #             "payment_preimage": payment_preimage,
    #             "hash_algorithm": "sha256",
    #         }
    #     )
    #     before_channel = self.fiber1.get_client().list_channels({})
    #
    #     self.fiber1.get_client().send_payment(
    #         {
    #             "invoice": invoice["invoice_address"],
    #         }
    #     )
    #     time.sleep(10)
    #     after_channel = self.fiber1.get_client().list_channels({})
    #     assert (
    #             int(before_channel["channels"][0]["local_balance"], 16)
    #             - int(after_channel["channels"][0]["local_balance"], 16)
    #             == int(invoice_balance, 16)
    #     )
    #
    #     # send 1 ckb again
    #     invoice_balance = hex(1 * 100000000)
    #     payment_preimage = generate_random_preimage()
    #
    #     invoice = self.fiber2.get_client().new_invoice(
    #         {
    #             "amount": invoice_balance,
    #             "currency": "Fibb",
    #             "description": "test invoice generated by node2",
    #             "expiry": "0xe10",
    #             "final_cltv": "0x28",
    #             "payment_preimage": payment_preimage,
    #             "hash_algorithm": "sha256",
    #         }
    #     )
    #     before_channel = self.fiber1.get_client().list_channels({})
    #
    #     self.fiber1.get_client().send_payment(
    #         {
    #             "invoice": invoice["invoice_address"],
    #         }
    #     )
    #     time.sleep(10)
    #     after_channel = self.fiber1.get_client().list_channels({})
    #     assert (
    #             int(before_channel["channels"][0]["local_balance"], 16)
    #             - int(after_channel["channels"][0]["local_balance"], 16)
    #             == int(invoice_balance, 16)
    #     )
    #
    #     # node2 send 1 ckb
    #     invoice_balance = hex(1 * 100000000)
    #     payment_preimage = generate_random_preimage()
    #     invoice = self.fiber1.get_client().new_invoice(
    #         {
    #             "amount": invoice_balance,
    #             "currency": "Fibb",
    #             "description": "test invoice generated by node2",
    #             "expiry": "0xe10",
    #             "final_cltv": "0x28",
    #             "payment_preimage": payment_preimage,
    #             "hash_algorithm": "sha256",
    #         }
    #     )
    #     time.sleep(1)
    #     print("node2 send 1 ckb failed ")
    #     before_channel_2 = self.fiber2.get_client().list_channels({})
    #     self.fiber2.get_client().send_payment(
    #         {
    #             "invoice": invoice["invoice_address"],
    #         }
    #     )
    #     time.sleep(10)
    #     after_channel_2 = self.fiber2.get_client().list_channels({})
    #     assert (
    #             int(before_channel_2["channels"][0]["local_balance"], 16)
    #             - int(after_channel_2["channels"][0]["local_balance"], 16)
    #             == int(invoice_balance, 16)
    #     )
    #
    #     # node2 send 1.00000001 ckb
    #     invoice_balance = hex(1 * 100000000 + 1)
    #     payment_preimage = generate_random_preimage()
    #
    #     invoice = self.fiber1.get_client().new_invoice(
    #         {
    #             "amount": invoice_balance,
    #             "currency": "Fibb",
    #             "description": "test invoice generated by node2",
    #             "expiry": "0xe10",
    #             "final_cltv": "0x28",
    #             "payment_preimage": payment_preimage,
    #             "hash_algorithm": "sha256",
    #         }
    #     )
    #     before_channel = self.fiber2.get_client().list_channels({})
    #
    #     with pytest.raises(Exception) as exc_info:
    #         self.fiber2.get_client().send_payment(
    #             {
    #                 "invoice": invoice["invoice_address"],
    #             }
    #         )
    #     expected_error_message = (
    #         "TemporaryChannelFailure"
    #     )
    #     assert expected_error_message in exc_info.value.args[0], (
    #         f"Expected substring '{expected_error_message}' "
    #         f"not found in actual string '{exc_info.value.args[0]}'"
    #     )
    #     channels = self.fiber1.get_client().list_channels(
    #         {"peer_id": self.fiber2.get_peer_id()}
    #     )
    #     N1N2_CHANNEL_ID = channels["channels"][0]["channel_id"]
    #     self.fiber1.get_client().graph_channels()
    #
    #     before_balance1 = self.Ckb_cli.wallet_get_capacity(
    #         self.account1["address"]["testnet"]
    #     )
    #     before_balance2 = self.Ckb_cli.wallet_get_capacity(
    #         self.account2["address"]["testnet"]
    #     )
    #     # shut down
    #     self.fiber1.get_client().shutdown_channel(
    #         {
    #             "channel_id": N1N2_CHANNEL_ID,
    #             "close_script": {
    #                 "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
    #                 "hash_type": "type",
    #                 "args": self.account1["lock_arg"],
    #             },
    #             "fee_rate": "0x3FC",
    #         }
    #     )
    #     # todo wait close tx commit
    #     time.sleep(20)
    #     after_balance1 = self.Ckb_cli.wallet_get_capacity(self.account1["address"]["testnet"])
    #     after_balance2 = self.Ckb_cli.wallet_get_capacity(
    #         self.account2["address"]["testnet"]
    #     )
    #     print("before_balance1:", before_balance1)
    #     print("before_balance2:", before_balance2)
    #     print("after_balance1:", after_balance1)
    #     print("after_balance2:", after_balance2)
    #     assert after_balance2 - before_balance2 == 63
    #
    # def test_udt_max_tlc_value_in_flight_not_eq_default(self):
    #     """
    #     max_tlc_value_in_flight != default
    #     Returns:
    #     """
    #     self.fiber1.connect_peer(self.fiber2)
    #     time.sleep(5)
    #     self.fiber1.get_client().open_channel(
    #         {
    #             "peer_id": self.fiber2.get_peer_id(),
    #             "funding_amount": hex(1000 * 100000000),
    #             "public": True,
    #             "max_tlc_value_in_flight": hex(1 * 100000000),
    #             "funding_udt_type_script": {
    #                 "code_hash": self.udtContract.get_code_hash(True, self.node.rpcUrl),
    #                 "hash_type": "type",
    #                 "args": self.udtContract.get_owner_arg_by_lock_arg(self.account1["lock_arg"]),
    #             },
    #             # "tlc_fee_proportional_millionths": "0x4B0",
    #         }
    #     )
    #
    #     time.sleep(1)
    #     wait_for_channel_state(
    #         self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
    #     )
    #     time.sleep(5)
    #     # transfer
    #     self.fiber1.get_client().graph_channels()
    #     self.fiber1.get_client().graph_nodes()
    #     payment_preimage = generate_random_preimage()
    #     channels = self.fiber1.get_client().list_channels({})
    #     # send 1.00000001 ckb
    #     invoice_balance = hex(1 * 100000000 + 1)
    #
    #     invoice = self.fiber2.get_client().new_invoice(
    #         {
    #             "amount": invoice_balance,
    #             "currency": "Fibb",
    #             "description": "test invoice generated by node2",
    #             "expiry": "0xe10",
    #             "final_cltv": "0x28",
    #             "payment_preimage": payment_preimage,
    #             "hash_algorithm": "sha256",
    #             "udt_type_script": {
    #                 "code_hash": self.udtContract.get_code_hash(True, self.node.rpcUrl),
    #                 "hash_type": "type",
    #                 "args": self.udtContract.get_owner_arg_by_lock_arg(self.account1["lock_arg"]),
    #             },
    #         }
    #     )
    #     before_channel = self.fiber1.get_client().list_channels({})
    #
    #     with pytest.raises(Exception) as exc_info:
    #         self.fiber1.get_client().send_payment(
    #             {
    #                 "invoice": invoice["invoice_address"],
    #             }
    #         )
    #     expected_error_message = (
    #         "TemporaryChannelFailure"
    #     )
    #     assert expected_error_message in exc_info.value.args[0], (
    #         f"Expected substring '{expected_error_message}' "
    #         f"not found in actual string '{exc_info.value.args[0]}'"
    #     )
    #     # send 1  ckb
    #     invoice_balance = hex(1 * 100000000)
    #     payment_preimage = generate_random_preimage()
    #
    #     invoice = self.fiber2.get_client().new_invoice(
    #         {
    #             "amount": invoice_balance,
    #             "currency": "Fibb",
    #             "description": "test invoice generated by node2",
    #             "expiry": "0xe10",
    #             "final_cltv": "0x28",
    #             "payment_preimage": payment_preimage,
    #             "hash_algorithm": "sha256",
    #             "udt_type_script": {
    #                 "code_hash": self.udtContract.get_code_hash(True, self.node.rpcUrl),
    #                 "hash_type": "type",
    #                 "args": self.udtContract.get_owner_arg_by_lock_arg(self.account1["lock_arg"]),
    #             },
    #         }
    #     )
    #     before_channel = self.fiber1.get_client().list_channels({})
    #
    #     self.fiber1.get_client().send_payment(
    #         {
    #             "invoice": invoice["invoice_address"],
    #         }
    #     )
    #     time.sleep(10)
    #     after_channel = self.fiber1.get_client().list_channels({})
    #     assert (
    #             int(before_channel["channels"][0]["local_balance"], 16)
    #             - int(after_channel["channels"][0]["local_balance"], 16)
    #             == int(invoice_balance, 16)
    #     )
    #
    #     # send 1 ckb again
    #     invoice_balance = hex(1 * 100000000)
    #     payment_preimage = generate_random_preimage()
    #
    #     invoice = self.fiber2.get_client().new_invoice(
    #         {
    #             "amount": invoice_balance,
    #             "currency": "Fibb",
    #             "description": "test invoice generated by node2",
    #             "expiry": "0xe10",
    #             "final_cltv": "0x28",
    #             "payment_preimage": payment_preimage,
    #             "hash_algorithm": "sha256",
    #             "udt_type_script": {
    #                 "code_hash": self.udtContract.get_code_hash(True, self.node.rpcUrl),
    #                 "hash_type": "type",
    #                 "args": self.udtContract.get_owner_arg_by_lock_arg(self.account1["lock_arg"]),
    #             },
    #         }
    #     )
    #     before_channel = self.fiber1.get_client().list_channels({})
    #
    #     self.fiber1.get_client().send_payment(
    #         {
    #             "invoice": invoice["invoice_address"],
    #         }
    #     )
    #     time.sleep(10)
    #     after_channel = self.fiber1.get_client().list_channels({})
    #     assert (
    #             int(before_channel["channels"][0]["local_balance"], 16)
    #             - int(after_channel["channels"][0]["local_balance"], 16)
    #             == int(invoice_balance, 16)
    #     )
    #
    #     # node2 send 1 ckb
    #     invoice_balance = hex(1 * 100000000)
    #     payment_preimage = generate_random_preimage()
    #     invoice = self.fiber1.get_client().new_invoice(
    #         {
    #             "amount": invoice_balance,
    #             "currency": "Fibb",
    #             "description": "test invoice generated by node2",
    #             "expiry": "0xe10",
    #             "final_cltv": "0x28",
    #             "payment_preimage": payment_preimage,
    #             "hash_algorithm": "sha256",
    #             "udt_type_script": {
    #                 "code_hash": self.udtContract.get_code_hash(True, self.node.rpcUrl),
    #                 "hash_type": "type",
    #                 "args": self.udtContract.get_owner_arg_by_lock_arg(self.account1["lock_arg"]),
    #             },
    #         }
    #     )
    #     time.sleep(1)
    #     print("node2 send 1 ckb failed ")
    #     before_channel_2 = self.fiber2.get_client().list_channels({})
    #     self.fiber2.get_client().send_payment(
    #         {
    #             "invoice": invoice["invoice_address"],
    #         }
    #     )
    #     time.sleep(10)
    #     after_channel_2 = self.fiber2.get_client().list_channels({})
    #     assert (
    #             int(before_channel_2["channels"][0]["local_balance"], 16)
    #             - int(after_channel_2["channels"][0]["local_balance"], 16)
    #             == int(invoice_balance, 16)
    #     )
    #
    #     # node2 send 1.00000001 ckb
    #     invoice_balance = hex(1 * 100000000 + 1)
    #     payment_preimage = generate_random_preimage()
    #
    #     invoice = self.fiber1.get_client().new_invoice(
    #         {
    #             "amount": invoice_balance,
    #             "currency": "Fibb",
    #             "description": "test invoice generated by node2",
    #             "expiry": "0xe10",
    #             "final_cltv": "0x28",
    #             "payment_preimage": payment_preimage,
    #             "hash_algorithm": "sha256",
    #             "udt_type_script": {
    #                 "code_hash": self.udtContract.get_code_hash(True, self.node.rpcUrl),
    #                 "hash_type": "type",
    #                 "args": self.udtContract.get_owner_arg_by_lock_arg(self.account1["lock_arg"]),
    #             },
    #         }
    #     )
    #     before_channel = self.fiber2.get_client().list_channels({})
    #
    #     with pytest.raises(Exception) as exc_info:
    #         self.fiber2.get_client().send_payment(
    #             {
    #                 "invoice": invoice["invoice_address"],
    #             }
    #         )
    #     expected_error_message = (
    #         "TemporaryChannelFailure"
    #     )
    #     assert expected_error_message in exc_info.value.args[0], (
    #         f"Expected substring '{expected_error_message}' "
    #         f"not found in actual string '{exc_info.value.args[0]}'"
    #     )
    #     channels = self.fiber1.get_client().list_channels(
    #         {"peer_id": self.fiber2.get_peer_id()}
    #     )
    #     N1N2_CHANNEL_ID = channels["channels"][0]["channel_id"]
    #     self.fiber1.get_client().graph_channels()
    #
    #     before_balance1 = self.Ckb_cli.wallet_get_capacity(
    #         self.account1["address"]["testnet"]
    #     )
    #     before_balance2 = self.Ckb_cli.wallet_get_capacity(
    #         self.account2["address"]["testnet"]
    #     )
    #     # shut down
    #     self.fiber1.get_client().shutdown_channel(
    #         {
    #             "channel_id": N1N2_CHANNEL_ID,
    #             "close_script": {
    #                 "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
    #                 "hash_type": "type",
    #                 "args": self.account1["lock_arg"],
    #             },
    #             "fee_rate": "0x3FC",
    #         }
    #     )
    #     # todo wait close tx commit
    #     time.sleep(20)
    #     after_balance1 = self.Ckb_cli.wallet_get_capacity(self.account1["address"]["testnet"])
    #     after_balance2 = self.Ckb_cli.wallet_get_capacity(
    #         self.account2["address"]["testnet"]
    #     )
    #     print("before_balance1:", before_balance1)
    #     print("before_balance2:", before_balance2)
    #     print("after_balance1:", after_balance1)
    #     print("after_balance2:", after_balance2)
    #     assert after_balance2 - before_balance2 == 143
    #     account2_balance = self.udtContract.list_cell(self.node.getClient(), own_arg=self.account1['lock_arg'],
    #                                                   query_arg=self.account2['lock_arg'])
    #     account1_balance = self.udtContract.list_cell(self.node.getClient(), own_arg=self.account1['lock_arg'],
    #                                                   query_arg=self.account1['lock_arg'])
    #     print("account1:", account1_balance)
    #     print("account2:", account2_balance)
    #     assert account1_balance[1]['balance'] == 99900000000
    #     assert account2_balance[0]['balance'] == 100000000

    # def test_max_tlc_number_in_flight_none(self):
    #     """
    #     max_tlc_number_in_flight == none
    #     Returns:
    #     """
    #     self.test_linked_peer()
    #
    # def test_max_tlc_number_in_flight_zero(self):
    #     """
    #     max_tlc_number_in_flight = 0
    #     Returns:
    #     """
    #     self.fiber1.connect_peer(self.fiber2)
    #     time.sleep(5)
    #     temporary_channel_id = self.fiber1.get_client().open_channel(
    #         {
    #             "peer_id": self.fiber2.get_peer_id(),
    #             "funding_amount": hex(200 * 100000000),
    #             "public": True,
    #             "max_tlc_number_in_flight": "0x0"
    #         }
    #     )
    #     time.sleep(1)
    #     wait_for_channel_state(
    #         self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
    #     )
    #     time.sleep(5)
    #     # transfer
    #     self.fiber1.get_client().graph_channels()
    #     self.fiber1.get_client().graph_nodes()
    #     payment_preimage = generate_random_preimage()
    #     invoice_balance = 100 * 100000000
    #     invoice = self.fiber2.get_client().new_invoice(
    #         {
    #             "amount": hex(invoice_balance),
    #             "currency": "Fibb",
    #             "description": "test invoice generated by node2",
    #             "expiry": "0xe10",
    #             "final_cltv": "0x28",
    #             "payment_preimage": payment_preimage,
    #             "hash_algorithm": "sha256",
    #         }
    #     )
    #     before_channel = self.fiber1.get_client().list_channels({})
    #
    #     with pytest.raises(Exception) as exc_info:
    #         self.fiber1.get_client().send_payment(
    #             {
    #                 "invoice": invoice["invoice_address"],
    #             }
    #         )
    #     expected_error_message = (
    #         "TemporaryChannelFailure"
    #     )
    #     assert expected_error_message in exc_info.value.args[0], (
    #         f"Expected substring '{expected_error_message}' "
    #         f"not found in actual string '{exc_info.value.args[0]}'"
    #     )
    #
    #     channels = self.fiber1.get_client().list_channels(
    #         {"peer_id": self.fiber2.get_peer_id()}
    #     )
    #     N1N2_CHANNEL_ID = channels["channels"][0]["channel_id"]
    #     self.fiber1.get_client().graph_channels()
    #
    #     before_balance1 = self.Ckb_cli.wallet_get_capacity(
    #         self.account1["address"]["testnet"]
    #     )
    #     before_balance2 = self.Ckb_cli.wallet_get_capacity(
    #         self.account2["address"]["testnet"]
    #     )
    #     # shut down
    #     self.fiber1.get_client().shutdown_channel(
    #         {
    #             "channel_id": N1N2_CHANNEL_ID,
    #             "close_script": {
    #                 "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
    #                 "hash_type": "type",
    #                 "args": self.account1["lock_arg"],
    #             },
    #             "fee_rate": "0x3FC",
    #         }
    #     )
    #     # todo wait close tx commit
    #     time.sleep(20)
    #     after_balance1 = self.Ckb_cli.wallet_get_capacity(self.account1["address"]["testnet"])
    #     after_balance2 = self.Ckb_cli.wallet_get_capacity(
    #         self.account2["address"]["testnet"]
    #     )
    #     print("before_balance1:", before_balance1)
    #     print("before_balance2:", before_balance2)
    #     print("after_balance1:", after_balance1)
    #     print("after_balance2:", after_balance2)
    #     assert after_balance2 - before_balance2 == 62
    #
    # def test_max_tlc_number_in_flight_not_eq_default(self):
    #     """
    #     max_tlc_number_in_flight != default
    #     Returns:
    #     """
    #     # max_tlc_number_in_flight_num = 15
    #     self.fiber1.connect_peer(self.fiber2)
    #     time.sleep(5)
    #     temporary_channel_id = self.fiber1.get_client().open_channel(
    #         {
    #             "peer_id": self.fiber2.get_peer_id(),
    #             "funding_amount": hex(200 * 100000000),
    #             "public": True,
    #             "max_tlc_number_in_flight": hex(16)
    #         }
    #     )
    #     time.sleep(1)
    #     wait_for_channel_state(
    #         self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
    #     )
    #     time.sleep(5)
    #     # transfer
    #     self.fiber1.get_client().graph_channels()
    #     self.fiber1.get_client().graph_nodes()
    #     channel_id = self.fiber1.get_client().list_channels({})['channels'][0]['channel_id']
    #     invoice_balance = 1 * 100000000
    #     invoice_list = []
    #     payment_preimage_list = []
    #     add_tlc_list = []
    #     remove_tlc_list = []
    #     invoice_count = 16
    #     for i in range(invoice_count):
    #         print("current :", i)
    #         payment_preimage = generate_random_preimage()
    #         add_tlc = self.fiber1.get_client().add_tlc({
    #             "channel_id": channel_id,
    #             "amount": hex(100),
    #             # "payment_hash": invoice_list[i]['invoice']['data']['payment_hash'],
    #             "payment_hash": payment_preimage,
    #             "expiry": 400,
    #             "hash_algorithm": "sha256"
    #         })
    #         add_tlc_list.append(add_tlc)
    #         # time.sleep(0.5)
    #     time.sleep(10)
    #     with pytest.raises(Exception) as exc_info:
    #         payment_preimage = generate_random_preimage()
    #         self.fiber1.get_client().add_tlc({
    #             "channel_id": channel_id,
    #             "amount": hex(100),
    #             # "payment_hash": invoice_list[i]['invoice']['data']['payment_hash'],
    #             "payment_hash": payment_preimage,
    #             "expiry": 400,
    #             "hash_algorithm": "sha256"
    #         })
    #     expected_error_message = (
    #         "TlcErrPacket"
    #     )
    #     assert expected_error_message in exc_info.value.args[0], (
    #         f"Expected substring '{expected_error_message}' "
    #         f"not found in actual string '{exc_info.value.args[0]}'"
    #     )
    #     self.fiber1.get_client().list_channels({})
    #     self.fiber2.get_client().list_channels({})

    # def test_open_chanel_same_time(self):
    #     """
    #     同时打开多个channel
    #     Returns:
    #     """
    #     open_count = 5
    #     self.new_fibers = []
    #     deploy_hash, deploy_index = self.udtContract.get_deploy_hash_and_index()
    #     for i in range(open_count):
    #         account3_private_key = generate_random_preimage()
    #         account3 = self.Ckb_cli.util_key_info_by_private_key(account3_private_key)
    #         tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(self.Config.ACCOUNT_PRIVATE_1,
    #                                                               account3["address"]["testnet"],
    #                                                               1000,
    #                                                               self.node.rpcUrl)
    #         self.Miner.miner_until_tx_committed(self.node, tx_hash)
    #         tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(self.Config.ACCOUNT_PRIVATE_1,
    #                                                               account3["address"]["testnet"],
    #                                                               1000,
    #                                                               self.node.rpcUrl)
    #         self.Miner.miner_until_tx_committed(self.node, tx_hash)
    #
    #         # start fiber3
    #         self.fiber3 = Fiber.init_by_port(
    #             FiberConfigPath.V100_DEV,
    #             account3_private_key,
    #             f"fiber/node{3 + i}",
    #             str(8251 + i),
    #             str(8302 + i),
    #         )
    #         self.fibers.append(self.fiber3)
    #         self.new_fibers.append(self.fiber3)
    #         self.fiber3.prepare(
    #             update_config={
    #                 "ckb_rpc_url": self.node.rpcUrl,
    #                 "ckb_udt_whitelist": True,
    #                 "xudt_script_code_hash": self.Contract.get_ckb_contract_codehash(
    #                     deploy_hash, deploy_index, True, self.node.rpcUrl
    #                 ),
    #                 "xudt_cell_deps_tx_hash": deploy_hash,
    #                 "xudt_cell_deps_index": deploy_index,
    #             }
    #         )
    #         self.fiber3.start(self.node)
    #         self.fiber3.connect_peer(self.fiber2)
    #     time.sleep(1)
    #     for i in range(open_count):
    #         self.new_fibers[i].get_client().open_channel(
    #             {
    #                 "peer_id": self.fiber2.get_peer_id(),
    #                 "funding_amount": hex(200 * 100000000),
    #                 "public": True,
    #             }
    #         )
    #         wait_for_channel_state(
    #             self.new_fibers[i].get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
    #         )
    #     for i in range(open_count):
    #         wait_for_channel_state(
    #             self.new_fibers[i].get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
    #         )
    #     send_payment_count = 10
    #     invoice_list = []
    #     for j in range(send_payment_count):
    #         print("current j:", j)
    #         invoice_list = []
    #
    #         for i in range(open_count):
    #             payment_preimage = generate_random_preimage()
    #             invoice_balance = 1
    #             invoice = self.fiber2.get_client().new_invoice(
    #                 {
    #                     "amount": hex(invoice_balance),
    #                     "currency": "Fibb",
    #                     "description": "test invoice generated by node2",
    #                     "expiry": "0xe10",
    #                     "final_cltv": "0x28",
    #                     "payment_preimage": payment_preimage,
    #                     "hash_algorithm": "sha256",
    #                 }
    #             )
    #             invoice_list.append(invoice)
    #         for i in range(open_count):
    #             self.new_fibers[i].get_client().send_payment(
    #                 {
    #                     "invoice": invoice_list[i]["invoice_address"],
    #                 }
    #             )
    #         for i in range(open_count):
    #             wait_for_channel_state(
    #                 self.new_fibers[i].get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
    #             )
