import time

from framework.basic import CkbTest
from framework.fiber_rpc import FiberRPCClient
from framework.test_fiber import Fiber, FiberConfigPath
from framework.util import generate_random_preimage


class TestFiber(CkbTest):
    cryptapeFiber1 = FiberRPCClient("http://18.163.221.211:8227")
    cryptapeFiber2 = FiberRPCClient("http://18.162.235.225:8227")

    ACCOUNT_PRIVATE_1 = "0xaae4515b745efcd6f00c1b40aaeef3dd66c82d75f8f43d0f18e1a1eecb90ada4"
    ACCOUNT_PRIVATE_2 = "0x518d76bbfe5ffe3a8ef3ad486e784ec333749575fb3c697126cdaa8084d42532"
    fiber1: Fiber
    fiber2: Fiber

    @classmethod
    def setup_class(cls):
        print("\nSetup TestClass2")
        cls.fiber1 = Fiber.init_by_port(
            FiberConfigPath.V100_TESTNET,
            cls.ACCOUNT_PRIVATE_1,
            "fiber/node1",
            "8228",
            "8227",
        )

        cls.fiber2 = Fiber.init_by_port(
            FiberConfigPath.V100_TESTNET,
            cls.ACCOUNT_PRIVATE_2,
            "fiber/node2",
            "8229",
            "8230",
        )

        # cls.fiber1.prepare()
        # cls.fiber1.start()
        cls.fiber1.get_client().connect_peer({
            "address": cls.cryptapeFiber1.node_info()["addresses"][0]})

        # cls.fiber2.prepare()
        # cls.fiber2.start()
        cls.fiber2.get_client().connect_peer({
            "address": cls.cryptapeFiber2.node_info()["addresses"][0]})
        time.sleep(1)


    def test_ckb(self):
        # open_channel
        temporary_channel_id = self.fiber1.get_client().open_channel(
            {
                "peer_id": self.cryptapeFiber1.get_peer_id(),
                "funding_amount": hex(500 * 100000000),
                "public": True,
                # "tlc_fee_proportional_millionths": "0x4B0",
            }
        )

        temporary_channel_id = self.fiber2.get_client().open_channel(
            {
                "peer_id": self.cryptapeFiber2.get_peer_id(),
                "funding_amount": hex(500 * 100000000),
                "public": True,
                # "tlc_fee_proportional_millionths": "0x4B0",
            }
        )
        wait_for_channel_state(
            self.fiber1.get_client(), self.cryptapeFiber1.get_peer_id(), "CHANNEL_READY", 120
        )

        wait_for_channel_state(
            self.fiber2.get_client(), self.cryptapeFiber1.get_peer_id(), "CHANNEL_READY", 120
        )

        # wait dry_run success
        send_payment(self.fiber1.get_client(), self.fiber2.get_client(), 1000, 9999999)
        send_payment(self.fiber2.get_client(), self.fiber1.get_client(), 1000, 9999999)

    def test_udt(self):
        pass
    def test_03(self):
        account = self.Ckb_cli.util_key_info_by_private_key(
            self.Config.ACCOUNT_PRIVATE_1
        )

        # start 2 fiber with xudt
        self.fiber1 = Fiber.init_by_port(
            FiberConfigPath.V100_TESTNET,
            self.Config.ACCOUNT_PRIVATE_1,
            "fiber/node1",
            "8228",
            "8227",
        )
        self.fiber2 = Fiber.init_by_port(
            FiberConfigPath.V100_TESTNET,
            self.Config.ACCOUNT_PRIVATE_2,
            "fiber/node2",
            "8229",
            "8230",
        )

        self.fiber1.get_client().graph_nodes()
        self.fiber2.get_client().graph_nodes()
        self.fiber1.get_client().graph_channels()
        self.fiber2.get_client().graph_channels()

    def test_02(self):
        account = self.Ckb_cli.util_key_info_by_private_key(
            self.Config.ACCOUNT_PRIVATE_1
        )

        # start 2 fiber with xudt
        self.fiber1 = Fiber.init_by_port(
            FiberConfigPath.V100,
            self.Config.ACCOUNT_PRIVATE_1,
            "fiber/node1",
            "8228",
            "8227",
        )
        self.fiber2 = Fiber.init_by_port(
            FiberConfigPath.V100,
            self.Config.ACCOUNT_PRIVATE_2,
            "fiber/node2",
            "8229",
            "8230",
        )
        self.fiber1.prepare()
        self.fiber1.start()
        self.fiber2.prepare()
        self.fiber2.start()
        # connect  2 fiber
        self.fiber1.connect_peer(self.fiber2)

        # open channel
        temporary_channel_id = self.fiber1.get_client().open_channel(
            {
                "peer_id": self.fiber2.get_peer_id(),
                "funding_amount": hex(1000 * 100000000),
                "public": True,
                # "tlc_fee_proportional_millionths": "0x4B0",
            }
        )
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


def send_payment(fiber1: FiberRPCClient, fiber2: FiberRPCClient, amount, udt=None, wait_times=300):
    try_times = 0
    payment = None
    for i in range(try_times):
        try:
            payment = fiber1.get_client().send_payment({
                "amount": hex(amount),
                "target_pubkey": fiber2.get_client().node_info()["node_id"],
                "keysend": True,
                "udt_type_script": udt
            })
            break
        except Exception as e:
            print(e)
            print(f"try count: {i}")
            time.sleep(1)
            continue

    for i in range(wait_times):
        time.sleep(1)
        try:
            payment = fiber1.get_payment(payment["payment_hash"])
            if payment["status"] == "Success":
                print("payment success")
                return payment
        except Exception as e:
            print(e)
            print(f"try count: {i}")
            continue
    raise TimeoutError("payment timeout")


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
