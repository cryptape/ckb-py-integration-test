import json
import time

from framework.basic import CkbTest
from framework.util import get_project_root


class TestIpcCall(CkbTest):

    @classmethod
    def setup_class(cls):
        """
        1. start node in issue/node1
        2. miner 400 block
        Returns:

        """

        # 1. start node in issue/node1
        node1 = cls.CkbNode.init_dev_by_port(
            cls.CkbNodeConfigPath.CURRENT_TEST, "ipc_call/node1", 8114, 8927
        )
        cls.node = node1
        node1.prepare(other_ckb_config={"ckb_rpc_modules": [
            "Net",
            "Pool",
            "Miner",
            "Chain",
            "Stats",
            "Subscription",
            "Experiment",
            "Debug",
            "IntegrationTest",
            "IPC"
        ]})
        node1.start()

        # 2. miner 400 block
        # cls.Miner.make_tip_height_number(cls.node, 400)
        cls.node.getClient().generate_epochs("0x2")
        time.sleep(3)
        cls.ipc_test_contract_tx_hash = cls.Contract.deploy_ckb_contract(
            cls.Config.ACCOUNT_PRIVATE_1,
            f"{get_project_root()}/source/contract/ipc_test/ipc_test"
        )
        cls.Miner.miner_until_tx_committed(cls.node, cls.ipc_test_contract_tx_hash)

        cls.ipc_test_with_exec_contract_tx_hash = cls.Contract.deploy_ckb_contract(
            cls.Config.ACCOUNT_PRIVATE_1,
            f"{get_project_root()}/source/contract/ipc_test/ipc_test_with_exec"
        )
        cls.Miner.miner_until_tx_committed(cls.node, cls.ipc_test_with_exec_contract_tx_hash)

        cls.ipc_test_with_spawn_contract_tx_hash = cls.Contract.deploy_ckb_contract(
            cls.Config.ACCOUNT_PRIVATE_1,
            f"{get_project_root()}/source/contract/ipc_test/ipc_test_with_spawn"
        )
        cls.Miner.miner_until_tx_committed(cls.node, cls.ipc_test_with_spawn_contract_tx_hash)

    @classmethod
    def teardown_class(cls):
        print("\nTeardown TestClass1")
        cls.node.stop()
        cls.node.clean()

    def test_call_math_add(self):
        # deploy math contract
        ipc_script_locator = {
            'out_point': {
                "index": "0x0",
                "tx_hash": self.ipc_test_contract_tx_hash
            }
        }
        ipc_req = {
            'version': '0x0',
            'method_id': '0x0',
            'payload_format': 'json',
            'payload': {
                'MathAdd': {'a': 2, 'b': 1},
            },
        }
        ipc_ret = self.node.getClient().ipc_call(ipc_script_locator, ipc_req)
        print(f'main: call result json={ipc_ret}')
        assert ipc_ret['payload']['MathAdd'] == 3

    def test_math_add_with_exec(self):
        account = self.Ckb_cli.util_key_info_by_private_key(self.Config.ACCOUNT_PRIVATE_1)
        father_tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(
            self.Config.ACCOUNT_PRIVATE_1,
            account["address"]["testnet"],
            100000,
            self.node.getClient().url
        )
        self.Miner.miner_until_tx_committed(self.node, father_tx_hash)

        tx = self.Tx.build_send_transfer_self_tx_with_input(
            [father_tx_hash],
            ["0x0"],
            self.Config.ACCOUNT_PRIVATE_1,
            output_count=15,
            fee=15000,
            api_url=self.node.getClient().url,
            dep_cells=[
                {"tx_hash": self.ipc_test_contract_tx_hash, "index_hex": hex(0)},
            ],
        )
        result = self.node.getClient().test_tx_pool_accept(tx, "passthrough")
        print("result:", result)
        #
        ipc_script_locator = {
            'out_point': {
                "index": "0x0",
                "tx_hash": self.ipc_test_with_exec_contract_tx_hash
            },
        }
        ipc_req = {
            'version': '0x0',
            'method_id': '0x0',
            'payload_format': 'json',
            'payload': {
                'MathAdd': {'a': 2, 'b': 1},
            },
        }
        ipc_env = {
            'tx': tx,
            'script_group_type': 'lock',
            'script_hash': account["lock_hash"]
        }
        ipc_call_result = self.node.getClient().ipc_call(ipc_script_locator, ipc_req, ipc_env)
        print("ipc_call_result:", ipc_call_result)
        assert ipc_call_result['payload']['MathAdd'] == 3

    def test_math_add_with_spawn(self):
        account = self.Ckb_cli.util_key_info_by_private_key(self.Config.ACCOUNT_PRIVATE_1)
        father_tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(
            self.Config.ACCOUNT_PRIVATE_1,
            account["address"]["testnet"],
            100000,
            self.node.getClient().url
        )
        self.Miner.miner_until_tx_committed(self.node, father_tx_hash)

        tx = self.Tx.build_send_transfer_self_tx_with_input(
            [father_tx_hash],
            ["0x0"],
            self.Config.ACCOUNT_PRIVATE_1,
            output_count=15,
            fee=15000,
            api_url=self.node.getClient().url,
            dep_cells=[
                {"tx_hash": self.ipc_test_with_spawn_contract_tx_hash, "index_hex": hex(0)},
            ],
        )
        result = self.node.getClient().test_tx_pool_accept(tx, "passthrough")
        print("result:", result)
        #
        ipc_script_locator = {
            'out_point': {
                "index": "0x0",
                "tx_hash": self.ipc_test_contract_tx_hash
            },
        }
        ipc_req = {
            'version': '0x0',
            'method_id': '0x0',
            'payload_format': 'json',
            'payload': {
                'Spawn': {'s': 'Hello'},
            },
        }
        ipc_env = {
            'tx': tx,
            'script_group_type': 'lock',
            'script_hash': account["lock_hash"]
        }
        ipc_call_result = self.node.getClient().ipc_call(ipc_script_locator, ipc_req, ipc_env)
        print("ipc_call_result:", ipc_call_result)
        assert ipc_call_result['payload']['Spawn'] == 'Hello'

    def test_math_add_with_hex(self):
        ipc_script_locator = {
            'out_point': {
                "index": "0x0",
                "tx_hash": self.ipc_test_contract_tx_hash
            },
        }
        ipc_req = {
            'version': '0x0',
            'method_id': '0x0',
            'payload_format': 'hex',
            'payload': '0x' + bytearray(json.dumps({
                'MathAdd': {'a': 2, 'b': 1},
            }).encode()).hex(),
        }
        ipc_ret = self.node.getClient().ipc_call(ipc_script_locator, ipc_req)
        print(f'main: call result data={ipc_ret}')
        assert json.loads(bytearray.fromhex(ipc_ret['payload'][2:]).decode())['MathAdd'] == 3

    def test_math_add_with_type_id_args(self):
        tx = self.node.getClient().get_transaction(self.ipc_test_contract_tx_hash)
        ipc_script_locator = {
            'type_id_args': tx["transaction"]["outputs"][0]["type"]["args"],
        }
        ipc_req = {
            'version': '0x0',
            'method_id': '0x0',
            'payload_format': 'json',
            'payload': {
                'MathAdd': {'a': 2, 'b': 1},
            },
        }
        ipc_ret = self.node.getClient().ipc_call(ipc_script_locator, ipc_req)
        print(f'main: call result json={ipc_ret}')
        assert ipc_ret['payload']['MathAdd'] == 3

    def test_test_call_syscall_load_script(self):
        tx = self.node.getClient().get_transaction(self.ipc_test_contract_tx_hash)
        ipc_script_locator = {
            'type_id_args': tx["transaction"]["outputs"][0]["type"]["args"],
        }

        ipc_script_locator = {
            'out_point': {
                "index": "0x0",
                "tx_hash": self.ipc_test_contract_tx_hash
            }
        }
        ipc_req = {
            'version': '0x0',
            'method_id': '0x0',
            'payload_format': 'json',
            'payload': {
                'SyscallLoadScript': {},
            },
        }
        ipc_ret = self.node.getClient().ipc_call(ipc_script_locator, ipc_req)

        # https://explorer.nervos.org/address/ckb1qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqp29j5z9tay5gqgqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqj34x52
        assert bytearray(ipc_ret['payload'][
                             'SyscallLoadScript']).hex() == "35000000100000003000000031000000b95123c71a870e3f0f74a7ee1dab8268dbfbc1407b46733ebd1b41f854b4324a0100000000"

    def test_test_call_syscall_load_script_with_env(self):
        account = self.Ckb_cli.util_key_info_by_private_key(self.Config.ACCOUNT_PRIVATE_1)
        father_tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(
            self.Config.ACCOUNT_PRIVATE_1,
            account["address"]["testnet"],
            100000,
            self.node.getClient().url
        )
        self.Miner.miner_until_tx_committed(self.node, father_tx_hash)

        tx = self.Tx.build_send_transfer_self_tx_with_input(
            [father_tx_hash],
            ["0x0"],
            self.Config.ACCOUNT_PRIVATE_1,
            output_count=15,
            fee=15000,
            api_url=self.node.getClient().url,
            dep_cells=[
                {"tx_hash": self.ipc_test_with_spawn_contract_tx_hash, "index_hex": hex(0)},
            ],
        )
        result = self.node.getClient().test_tx_pool_accept(tx, "passthrough")
        print("result:", result)
        #
        ipc_script_locator = {
            'out_point': {
                "index": "0x0",
                "tx_hash": self.ipc_test_contract_tx_hash
            },
        }
        ipc_req = {
            'version': '0x0',
            'method_id': '0x0',
            'payload_format': 'json',
            'payload': {
                'SyscallLoadScript': {},
            },
        }
        ipc_env = {
            'tx': tx,
            'script_group_type': 'lock',
            'script_hash': account["lock_hash"]
        }
        ipc_call_result = self.node.getClient().ipc_call(ipc_script_locator, ipc_req, ipc_env)
        assert f"490000001000000030000000310000009bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce80114000000{account['lock_arg'][2:]}" == bytearray(
            ipc_call_result['payload']['SyscallLoadScript']).hex()
