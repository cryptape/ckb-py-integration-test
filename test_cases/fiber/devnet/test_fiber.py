import time

from framework.basic import CkbTest
from framework.helper.udt_contract import UdtContract
from framework.test_fiber import Fiber, FiberConfigPath
from framework.util import generate_random_preimage, ckb_hash_script


class TestFiber(CkbTest):

    @classmethod
    def setup_class(cls):
        account = cls.Ckb_cli.util_key_info_by_private_key(cls.Config.ACCOUNT_PRIVATE_1)
        account2 = cls.Ckb_cli.util_key_info_by_private_key(
            cls.Config.ACCOUNT_PRIVATE_2
        )
        cls.node = cls.CkbNode.init_dev_by_port(
            cls.CkbNodeConfigPath.CURRENT_FIBER, "contract/node", 8114, 8115
        )
        cls.node.prepare()
        cls.node.start()
        cls.node.getClient().get_consensus()
        cls.Miner.make_tip_height_number(cls.node, 20)
        # deploy xudt
        xudt_contract_hash = cls.node.getClient().get_block_by_number("0x0")[
            "transactions"
        ][0]["hash"]

        cls.udtContract = UdtContract(xudt_contract_hash, 10)

        deploy_hash, deploy_index = cls.udtContract.get_deploy_hash_and_index()

        # # issue
        invoke_arg, invoke_data = cls.udtContract.issue(
            account["lock_arg"], 1000 * 100000000
        )
        tx_hash = cls.Contract.invoke_ckb_contract(
            account_private=cls.Config.ACCOUNT_PRIVATE_1,
            contract_out_point_tx_hash=deploy_hash,
            contract_out_point_tx_index=deploy_index,
            type_script_arg=invoke_arg,
            hash_type="type",
            data=invoke_data,
            fee=1000,
            api_url=cls.node.getClient().url,
            output_lock_arg=account["lock_arg"],
        )
        cls.Miner.miner_until_tx_committed(cls.node, tx_hash)
        cls.node.start_miner()
        # deploy fiber
        # start 2 fiber with xudt
        cls.fiber1 = Fiber.init_by_port(
            FiberConfigPath.V100_DEV,
            cls.Config.ACCOUNT_PRIVATE_1,
            "fiber/node1",
            "8228",
            "8227",
        )
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

        cls.fiber2 = Fiber.init_by_port(
            FiberConfigPath.V100_DEV,
            cls.Config.ACCOUNT_PRIVATE_2,
            "fiber/node2",
            "8229",
            "8230",
        )
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
        before_balance1 = cls.Ckb_cli.wallet_get_capacity(account["address"]["testnet"])
        print("before_balance1:", before_balance1)
        before_live_cells = cls.Ckb_cli.wallet_get_live_cells(
            account["address"]["testnet"]
        )
        print("before_live_cells:", before_live_cells)

        before_balance2 = cls.Ckb_cli.wallet_get_capacity(
            account2["address"]["testnet"]
        )
        print("before_balance2:", before_balance2)

        #

    @classmethod
    def teardown_class(cls):
        cls.node.stop()
        cls.node.clean()
        cls.fiber1.stop()
        cls.fiber1.clean()

        cls.fiber2.stop()
        cls.fiber2.clean()

    def test_udt(self):
        """
        1. 建立 udt channel
        2. 转账
        3. close channel
        4. 检查余额
        Returns:

        """
        # open chanel for fiber
        account = self.Ckb_cli.util_key_info_by_private_key(
            self.Config.ACCOUNT_PRIVATE_1
        )
        account2 = self.Ckb_cli.util_key_info_by_private_key(
            self.Config.ACCOUNT_PRIVATE_2
        )
        # connect  2 fiber
        self.fiber1.connect_peer(self.fiber2)
        # todo wait peer connet
        time.sleep(1)
        # open channel
        temporary_channel_id = self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(1000 * 100000000),
                "public": True,
                "funding_udt_type_script": {
                    "code_hash": self.udtContract.get_code_hash(True, self.node.rpcUrl),
                    "hash_type": "type",
                    "args": ckb_hash_script(account["lock_arg"]),
                },
                # "tlc_fee_proportional_millionths": "0x4B0",
            }
        )
        time.sleep(1)
        wait_for_channel_state(
            self.fiber1.get_client(), self.fiber2.get_peer_id(), "CHANNEL_READY", 120
        )
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
                "udt_type_script": {
                    "code_hash": self.udtContract.get_code_hash(True, self.node.rpcUrl),
                    "hash_type": "type",
                    "args": ckb_hash_script(account["lock_arg"]),
                },
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

        before_account1 = self.udtContract.list_cell(
            self.node.getClient(), account["lock_arg"], account["lock_arg"]
        )
        before_account2 = self.udtContract.list_cell(
            self.node.getClient(), account["lock_arg"], account2["lock_arg"]
        )
        # shut down
        self.fiber1.get_client().shutdown_channel(
            {
                "channel_id": N1N2_CHANNEL_ID,
                "close_script": {
                    "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
                    "hash_type": "type",
                    "args": account["lock_arg"],
                },
                "fee_rate": "0x3FC",
            }
        )
        # todo wait close txx commit
        time.sleep(20)

        after_account1 = self.udtContract.list_cell(
            self.node.getClient(), account["lock_arg"], account["lock_arg"]
        )
        after_account2 = self.udtContract.list_cell(
            self.node.getClient(), account["lock_arg"], account2["lock_arg"]
        )

        print(before_account1)
        assert before_account1[0]["balance"] == 0
        print(before_account2)
        assert len(before_account2) == 0
        print(after_account1)
        assert after_account1[1]["balance"] == 90000000000
        print(after_account2)
        assert after_account2[0]["balance"] == 10000000000
        before_balance1 = self.Ckb_cli.wallet_get_live_cells(
            account["address"]["testnet"]
        )
        print("before_balance1:", before_balance1)

    def test_ckb(self):
        """
        1. 建立 ckb channel
        2. 转账
        3. close channel
        4. 检查余额
        Returns:
        """
        account = self.Ckb_cli.util_key_info_by_private_key(
            self.Config.ACCOUNT_PRIVATE_1
        )
        account2 = self.Ckb_cli.util_key_info_by_private_key(
            self.Config.ACCOUNT_PRIVATE_2
        )
        # connect  2 fiber
        self.fiber1.connect_peer(self.fiber2)
        # todo wait peer connet
        time.sleep(1)
        account_balance = self.Ckb_cli.wallet_get_live_cells(
            account["address"]["testnet"]
        )
        print("accout balance :", account_balance)
        account_balance2 = self.Ckb_cli.wallet_get_live_cells(
            account2["address"]["testnet"]
        )
        print("accout balance2 :", account_balance2)

        # open channel
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

        # shut down
        self.fiber1.get_client().shutdown_channel(
            {
                "channel_id": N1N2_CHANNEL_ID,
                "close_script": {
                    "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
                    "hash_type": "type",
                    "args": account["lock_arg"],
                },
                "fee_rate": "0x3FC",
            }
        )
        before_balance1 = self.Ckb_cli.wallet_get_capacity(
            account["address"]["testnet"]
        )
        before_balance2 = self.Ckb_cli.wallet_get_capacity(
            account2["address"]["testnet"]
        )
        # todo wait close tx commit
        time.sleep(20)
        after_balance1 = self.Ckb_cli.wallet_get_capacity(account["address"]["testnet"])
        after_balance2 = self.Ckb_cli.wallet_get_capacity(
            account2["address"]["testnet"]
        )
        print("before_balance1:", before_balance1)
        print("before_balance2:", before_balance2)
        print("after_balance1:", after_balance1)
        print("after_balance2:", after_balance2)


def wait_for_channel_state(client, peer_id, expected_state, timeout=120):
    """Wait for a channel to reach a specific state."""
    for _ in range(timeout):
        channels = client.list_channels({"peer_id": peer_id})
        if channels["channels"][0]["state"]["state_name"] == expected_state:
            print(f"Channel reached expected state: {expected_state}")
            return channels["channels"][0]["channel_id"]
        print(
            f"Waiting for channel state: {expected_state}, current state: {channels['channels'][0]['state']['state_name']}"
        )
        time.sleep(1)
    raise TimeoutError(
        f"Channel did not reach state {expected_state} within timeout period."
    )
