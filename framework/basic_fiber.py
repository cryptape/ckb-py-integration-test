from framework.basic import CkbTest
import socket

from framework.helper.udt_contract import UdtContract, issue_udt_tx
from framework.test_fiber import Fiber, FiberConfigPath
from framework.util import generate_account_privakey
import time
import random
import datetime


class FiberTest(CkbTest):
    # deploy
    new_fibers: [Fiber] = []
    fibers: [Fiber] = []
    fiber1: Fiber
    fiber2: Fiber
    debug = False
    first_debug = False

    @classmethod
    def setup_class(cls):
        """
        部署一个ckb 节点
        启动 ckb 节点

        Returns:

        """
        cls.account1_private_key = cls.Config.ACCOUNT_PRIVATE_1
        cls.account2_private_key = cls.Config.ACCOUNT_PRIVATE_2
        cls.account1 = cls.Ckb_cli.util_key_info_by_private_key(
            cls.account1_private_key
        )
        cls.account2 = cls.Ckb_cli.util_key_info_by_private_key(
            cls.account2_private_key
        )
        cls.node = cls.CkbNode.init_dev_by_port(
            cls.CkbNodeConfigPath.CURRENT_FIBER, "contract/node", 8114, 8115
        )

        if cls.debug:
            if check_port(8114):
                print("=====不是第一次启动=====")
                return
            cls.debug = False
            print("====debug====第一次启动=")
            cls.first_debug = True

        cls.node.prepare()
        cls.node.start()
        cls.node.getClient().get_consensus()
        cls.Miner.make_tip_height_number(cls.node, 20)

    def setup_method(cls, method):
        """
        启动2个fiber
        给 fiber1 充值udt 金额
        连接2个fiber
        Args:
            method:

        Returns:

        """
        cls.did_pass = None
        cls.fibers = []
        cls.new_fibers = []
        cls.fiber1 = Fiber.init_by_port(
            FiberConfigPath.V100_DEV,
            cls.account1_private_key,
            "fiber/node1",
            "8228",
            "8227",
        )
        cls.fiber2 = Fiber.init_by_port(
            FiberConfigPath.V100_DEV,
            cls.account2_private_key,
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

        if cls.debug:
            return
            # # issue
        tx_hash = issue_udt_tx(
            cls.udtContract,
            cls.node.rpcUrl,
            cls.fiber1.account_private,
            cls.fiber1.account_private,
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
        if self.debug:
            return
        if self.first_debug:
            return
        super().teardown_method(method)
        for fiber in self.fibers:
            fiber.stop()
            fiber.clean()

    @classmethod
    def teardown_class(cls):
        if cls.debug:
            return
        if cls.first_debug:
            return
        cls.node.stop()
        cls.node.clean()

    def faucet(
        self,
        account_private_key,
        ckb_balance,
        udt_owner_private_key=None,
        udt_balance=1000 * 1000000000,
    ):
        if ckb_balance > 60:
            account = self.Ckb_cli.util_key_info_by_private_key(account_private_key)
            tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(
                self.Config.ACCOUNT_PRIVATE_1,
                account["address"]["testnet"],
                ckb_balance,
                self.node.rpcUrl,
            )
            self.Miner.miner_until_tx_committed(self.node, tx_hash)

        if udt_owner_private_key is None:
            return account_private_key
        tx_hash = issue_udt_tx(
            self.udtContract,
            self.node.rpcUrl,
            udt_owner_private_key,
            account_private_key,
            udt_balance,
        )
        self.Miner.miner_until_tx_committed(self.node, tx_hash)

    def generate_account(
        self, ckb_balance, udt_owner_private_key=None, udt_balance=1000 * 1000000000
    ):
        # error
        # if self.debug:
        #     raise Exception("debug not support generate_account")
        account_private_key = generate_account_privakey()
        self.faucet(
            account_private_key, ckb_balance, udt_owner_private_key, udt_balance
        )
        return account_private_key

    def start_new_mock_fiber(self, account_private_key, config=None):
        i = len(self.new_fibers)
        fiber = Fiber.init_by_port(
            FiberConfigPath.V100_DEV,
            account_private_key,
            f"fiber/node{3 + i}",
            str(8251 + i),
            str(8302 + i),
        )
        fiber.read_ckb_key()
        self.new_fibers.append(fiber)
        self.fibers.append(fiber)
        return fiber

    def start_new_fiber(self, account_private_key, config=None):
        if self.debug:
            print("=================start  mock fiber ==================")
            return self.start_new_mock_fiber(account_private_key, config)
        update_config = config
        if config is None:
            deploy_hash, deploy_index = self.udtContract.get_deploy_hash_and_index()
            update_config = {
                "ckb_rpc_url": self.node.rpcUrl,
                "ckb_udt_whitelist": True,
                "xudt_script_code_hash": self.Contract.get_ckb_contract_codehash(
                    deploy_hash, deploy_index, True, self.node.rpcUrl
                ),
                "xudt_cell_deps_tx_hash": deploy_hash,
                "xudt_cell_deps_index": deploy_index,
            }

        i = len(self.new_fibers)
        # start fiber3
        fiber = Fiber.init_by_port(
            FiberConfigPath.V100_DEV,
            account_private_key,
            f"fiber/node{3 + i}",
            str(8251 + i),
            str(8302 + i),
        )
        self.fibers.append(fiber)
        self.new_fibers.append(fiber)
        fiber.prepare(update_config=update_config)
        fiber.start(self.node)
        return fiber

    def wait_for_channel_state(self, client, peer_id, expected_state, timeout=120):
        """Wait for a channel to reach a specific state."""
        for _ in range(timeout):
            channels = client.list_channels({"peer_id": peer_id})
            if len(channels["channels"]) == 0:
                time.sleep(1)
                continue
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

    def get_account_udt_script(self, account_private_key):
        account1 = self.Ckb_cli.util_key_info_by_private_key(account_private_key)
        return {
            "code_hash": self.udtContract.get_code_hash(True, self.node.rpcUrl),
            "hash_type": "type",
            "args": self.udtContract.get_owner_arg_by_lock_arg(account1["lock_arg"]),
        }

    def get_account_script(self, account_private_key):
        account1 = self.Ckb_cli.util_key_info_by_private_key(account_private_key)
        return {
            "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
            "hash_type": "type",
            "args": account1["lock_arg"],
        }

    def wait_payment_state(self, client, payment_hash, status="Success", timeout=120):
        for i in range(timeout):
            result = client.get_client().get_payment({"payment_hash": payment_hash})
            if result["status"] == status:
                return
            time.sleep(1)
        raise TimeoutError(
            f"status did not reach state {expected_state} within timeout period."
        )

    def get_fiber_env(self, new_fiber_count=0):
        # print ckb tip number
        for i in range(new_fiber_count):
            self.start_new_mock_fiber("")
        node_tip_number = self.node.getClient().get_tip_block_number()
        # print fiber data
        fibers_data = []

        for i in range(len(self.fibers)):
            account_capacity = self.Ckb_cli.wallet_get_capacity(
                self.fibers[i].get_account()["address"]["testnet"]
            )
            node_info = self.fibers[i].get_client().node_info()
            channels = self.fibers[i].get_client().list_channels({})
            udt_cells = self.udtContract.list_cell(
                self.node.getClient(),
                self.get_account_script(self.fiber1.account_private)["args"],
                self.get_account_script(self.fibers[i].account_private)["args"],
            )

            fibers_data.append(
                {
                    "account_capacity": account_capacity,
                    "udt_cell": udt_cells,
                    "node_info": node_info,
                    "channels": channels["channels"],
                }
            )
        print("============================================================")
        print("======================== Fiber Env =========================")
        print("============================================================")
        print(f"ckb node url: {self.node.rpcUrl}, tip number: {node_tip_number}")
        for i in range(len(self.fibers)):
            print(f"--- current fiber: {i}----")
            print(f"url:{self.fibers[i].client.url}")
            print(
                f"account private key: {self.fibers[i].account_private}, ckb balance: {fibers_data[i]['account_capacity']} ,udt balance: {fibers_data[i]['udt_cell']}"
            )
            print(f"path:{self.fibers[i].tmp_path}")
            node_info = fibers_data[i]["node_info"]
            print(
                f"commit_hash:{node_info['commit_hash']}",
            )
            print(f"public_key:{node_info['public_key']}")
            print(f"peer_id:{node_info['peer_id']}")
            print(f"channel_count:{int(node_info['channel_count'], 16)}")
            print(f"peers_count:{int(node_info['peers_count'], 16)}")
            print(
                f"pending_channel_count:{int(node_info['pending_channel_count'], 16)}"
            )
            channels = fibers_data[i]["channels"]
            for channel in channels:
                channel_id = channel["channel_id"]
                peer_id = channel["peer_id"]
                state_name = channel["state"]["state_name"]
                local_balance = int(channel["local_balance"], 16) / 100000000
                offered_tlc_balance = (
                    int(channel["offered_tlc_balance"], 16) / 100000000
                )
                remote_balance = int(channel["remote_balance"], 16) / 100000000
                received_tlc_balance = (
                    int(channel["received_tlc_balance"], 16) / 100000000
                )
                created_at_hex = int(channel["created_at"], 16) / 1000000
                created_at = datetime.datetime.fromtimestamp(created_at_hex).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

                # 打印结果
                print(f"-----Channel ID: {channel_id}-------")
                print(f"Peer ID: {peer_id}")
                print(f"State: {state_name}")
                print(f"Local Balance: {local_balance}")
                print(f"Offered TLC Balance: {offered_tlc_balance}")
                print(f"Remote Balance: {remote_balance}")
                print(f"Received TLC Balance: {received_tlc_balance}")
                print(f"Created At: {created_at}")
                print("-" * 40)

    def get_fiber_message(self, fiber):
        channels = fiber.get_client().list_channels({})
        channels = channels["channels"]
        node_info = fiber.get_client().node_info()
        graph_channels = fiber.get_client().graph_channels()
        graph_nodes = fiber.get_client().graph_nodes()
        print(
            f"commit_hash:{node_info['commit_hash']}",
        )
        print(f"public_key:{node_info['public_key']}")
        print(f"peer_id:{node_info['peer_id']}")
        print(f"channel_count:{int(node_info['channel_count'], 16)}")
        print(f"peers_count:{int(node_info['peers_count'], 16)}")
        print(f"pending_channel_count:{int(node_info['pending_channel_count'], 16)}")
        print("---------channel------")
        # 处理每个通道
        for channel in channels:
            channel_id = channel["channel_id"]
            peer_id = channel["peer_id"]
            state_name = channel["state"]["state_name"]
            local_balance = int(channel["local_balance"], 16) / 100000000
            offered_tlc_balance = int(channel["offered_tlc_balance"], 16) / 100000000
            remote_balance = int(channel["remote_balance"], 16) / 100000000
            received_tlc_balance = int(channel["received_tlc_balance"], 16) / 100000000
            created_at_hex = int(channel["created_at"], 16) / 1000000
            created_at = datetime.datetime.fromtimestamp(created_at_hex).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            # 打印结果
            print(f"Channel ID: {channel_id}")
            print(f"Peer ID: {peer_id}")
            print(f"State: {state_name}")
            print(f"Local Balance: {local_balance}")
            print(f"Offered TLC Balance: {offered_tlc_balance}")
            print(f"Remote Balance: {remote_balance}")
            print(f"Received TLC Balance: {received_tlc_balance}")
            print(f"Created At: {created_at}")
            print("-" * 40)

    def generate_random_preimage(self):
        hash_str = "0x"
        for _ in range(64):
            hash_str += hex(random.randint(0, 15))[2:]
        return hash_str


def check_port(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)  # 设置超时时间为1秒
        try:
            s.connect(("127.0.0.1", port))
            return True  # 端口开放
        except (socket.timeout, socket.error):
            return False  # 端口未开放
