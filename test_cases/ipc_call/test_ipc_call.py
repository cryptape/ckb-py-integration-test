import hashlib
import json
import random
import string
import time

import pytest

from framework.basic import CkbTest
from framework.helper.udt_contract import UdtContract
from framework.util import get_project_root


class TestIpcCall(CkbTest):

    @classmethod
    def setup_class(cls):
        """
        1. start node in issue/node1
        2. generate 2 epoch
        Returns:

        """

        # 1. start node in issue/node1
        node1 = cls.CkbNode.init_dev_by_port(
            cls.CkbNodeConfigPath.CURRENT_TEST, "ipc_call/node1", 8114, 8927
        )
        cls.node = node1
        node1.prepare(
            other_ckb_config={
                "ckb_rpc_modules": [
                    "Net",
                    "Pool",
                    "Miner",
                    "Chain",
                    "Stats",
                    "Subscription",
                    "Experiment",
                    "Debug",
                    "IntegrationTest",
                    "IPC",
                ]
            }
        )
        node1.start()

        # 2. miner 400 block
        # cls.Miner.make_tip_height_number(cls.node, 400)
        cls.node.getClient().generate_epochs("0x2")
        time.sleep(3)
        cls.ipc_test_contract_tx_hash = cls.Contract.deploy_ckb_contract(
            cls.Config.ACCOUNT_PRIVATE_1,
            f"{get_project_root()}/source/contract/ipc_test/ipc_test",
        )
        cls.Miner.miner_until_tx_committed(cls.node, cls.ipc_test_contract_tx_hash)

        cls.ipc_test_with_exec_contract_tx_hash = cls.Contract.deploy_ckb_contract(
            cls.Config.ACCOUNT_PRIVATE_1,
            f"{get_project_root()}/source/contract/ipc_test/ipc_test_with_exec",
        )
        cls.Miner.miner_until_tx_committed(
            cls.node, cls.ipc_test_with_exec_contract_tx_hash
        )

        cls.ipc_test_with_spawn_contract_tx_hash = cls.Contract.deploy_ckb_contract(
            cls.Config.ACCOUNT_PRIVATE_1,
            f"{get_project_root()}/source/contract/ipc_test/ipc_test_with_spawn",
        )
        cls.Miner.miner_until_tx_committed(
            cls.node, cls.ipc_test_with_spawn_contract_tx_hash
        )

    @classmethod
    def teardown_class(cls):
        print("\nTeardown TestClass1")
        cls.node.stop()
        cls.node.clean()

    def test_not_spawn_serve(self):
        """
         存在的out_point，但不是spawn serve 合约，预期: 执行失败
         不存在的out_point，预期：失败
        Returns:
        """

        block = self.node.getClient().get_block_by_number("0x0")
        ipc_script_locator = {
            "out_point": {"index": "0x0", "tx_hash": block["transactions"][0]["hash"]}
        }
        ipc_req = {
            "version": "0x0",
            "method_id": "0x0",
            "payload_format": "json",
            "payload": {
                "MathAdd": {"a": 2, "b": 1},
            },
        }

        with pytest.raises(Exception) as exc_info:
            ipc_ret = self.node.getClient().ipc_call(ipc_script_locator, ipc_req)
        expected_error_message = "sending on a closed channel"
        assert (
            expected_error_message in exc_info.value.args[0]
        ), f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

        # 不存在的out_point
        ipc_script_locator = {
            "out_point": {
                "index": "0x0",
                "tx_hash": "0x000867a5e09eebdedecaa0437455e54d99f9c6752adad1fd299bd6ede303f461",
            }
        }
        with pytest.raises(Exception) as exc_info:
            ipc_ret = self.node.getClient().ipc_call(ipc_script_locator, ipc_req)
        expected_error_message = "Get out point failed: OutPoint"
        assert (
            expected_error_message in exc_info.value.args[0]
        ), f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

    def test_type_script_args_not_spawn_contract(self):
        """
        存在的 type script args，但不是spawn serve 合约，预期: 执行失败

        Returns:
        """
        udtContract = UdtContract()
        udtContract.deploy(self.Config.ACCOUNT_PRIVATE_1, self.node)
        deploy_hash, deploy_index = udtContract.get_deploy_hash_and_index()
        ipc_script_locator = {
            "out_point": {"index": hex(deploy_index), "tx_hash": deploy_hash}
        }
        ipc_req = {
            "version": "0x0",
            "method_id": "0x0",
            "payload_format": "json",
            "payload": {
                "MathAdd": {"a": 2, "b": 1},
            },
        }

        with pytest.raises(Exception) as exc_info:
            ipc_ret = self.node.getClient().ipc_call(ipc_script_locator, ipc_req)
        expected_error_message = "sending on a closed channel"
        assert (
            expected_error_message in exc_info.value.args[0]
        ), f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

    def test_death_cell(self):
        """
        已经被消费的out_point，但是spawn serve 合约，调用serve方法，预期: 成功
        Returns:
        """
        rand_account_private = (
            "0x000c06bfd800d27397002dca6fb0993d5ba6399b4238b2f29ee9deb97593d2bc"
        )
        rand_account = self.Ckb_cli.util_key_info_by_private_key(rand_account_private)
        ipc_test_data_contract_tx_hash = self.Contract.deploy_ckb_contract(
            self.Config.ACCOUNT_PRIVATE_1,
            f"{get_project_root()}/source/contract/ipc_test/ipc_test",
            2000,
            False,
            self.node.getClient().url,
            rand_account["address"]["testnet"],
        )
        self.Miner.miner_until_tx_committed(self.node, ipc_test_data_contract_tx_hash)
        # deploy math contract
        ipc_script_locator = {
            "out_point": {"index": "0x0", "tx_hash": ipc_test_data_contract_tx_hash}
        }

        ipc_req = {
            "version": "0x0",
            "method_id": "0x0",
            "payload_format": "json",
            "payload": {
                "MathAdd": {"a": 2, "b": 1},
            },
        }
        print("first ipc")
        live_cell = self.node.getClient().get_live_cell(
            "0x0", ipc_test_data_contract_tx_hash
        )
        print("live_cell:", live_cell)
        ipc_ret = self.node.getClient().ipc_call(ipc_script_locator, ipc_req)
        print(f"main1: call result json={ipc_ret}")
        assert ipc_ret["payload"]["MathAdd"] == 3

        # cost ipc_test_data_contract_tx_hash
        tx_hash = self.Tx.send_transfer_self_tx_with_input(
            [ipc_test_data_contract_tx_hash],
            ["0x0"],
            rand_account_private,
            output_count=1,
            fee=1090,
            api_url=self.node.getClient().url,
        )
        self.Miner.miner_until_tx_committed(self.node, tx_hash)
        live_cell = self.node.getClient().get_live_cell(
            "0x0", ipc_test_data_contract_tx_hash
        )
        print("live_cell:", live_cell)
        ipc_ret = self.node.getClient().ipc_call(ipc_script_locator, ipc_req)
        print(f"main: call result json={ipc_ret}")

    def test_call_payload_empty(self):
        """
        测试空 payload,预期：失败，IPC: EOF while parsing a value at line 1 column 0

        Returns:

        """
        # deploy math contract
        ipc_script_locator = {
            "out_point": {"index": "0x0", "tx_hash": self.ipc_test_contract_tx_hash}
        }
        ipc_req = {
            "version": "0x0",
            "method_id": "0x0",
            "payload_format": "json",
            "payload": {
                # "MathAdd": {"a": 2, "b": 1},
            },
        }

        with pytest.raises(Exception) as exc_info:
            ipc_ret = self.node.getClient().ipc_call(ipc_script_locator, ipc_req)
        expected_error_message = "IPC: EOF while parsing a value at line 1 column 0"
        assert (
            expected_error_message in exc_info.value.args[0]
        ), f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

    def test_call_math_add(self):
        """
        存在的out_point，并且是spawn serve 合约，调用serve方法，预期: 执行成功
        测试默认值（0）,预期: 执行成功
        "json" 模式下传递 JSON 对象
        Returns:

        """
        # deploy math contract
        ipc_script_locator = {
            "out_point": {"index": "0x0", "tx_hash": self.ipc_test_contract_tx_hash}
        }
        ipc_req = {
            "version": "0x0",
            "method_id": "0x0",
            "payload_format": "json",
            "payload": {
                "MathAdd": {"a": 2, "b": 1},
            },
        }
        ipc_ret = self.node.getClient().ipc_call(ipc_script_locator, ipc_req)
        print(f"main: call result json={ipc_ret}")
        assert ipc_ret["payload"]["MathAdd"] == 3

    def test_IpcRequest_version_and_method_id_not_eq_0x(self):
        """
        version 测试不存在的版本号（如 999），预期报错或 fallback
        method_id 填写任意值都可以，预期：成功
        Returns:

        """
        # deploy math contract
        ipc_script_locator = {
            "out_point": {"index": "0x0", "tx_hash": self.ipc_test_contract_tx_hash}
        }
        ipc_req = {
            "version": "0xff",
            "method_id": "0x1213",
            "payload_format": "json",
            "payload": {
                "MathAdd": {"a": 2, "b": 1},
            },
        }
        ipc_ret = self.node.getClient().ipc_call(ipc_script_locator, ipc_req)
        print(f"main: call result json={ipc_ret}")
        assert ipc_ret["payload"]["MathAdd"] == 3

    def test_math_add_with_exec(self):
        """
        exec 调用spawn server
        lock 合约，预期：成功
        存在匹配的script_hash，预期：成功
        通过校验的tx，预期：成功
        调用合约执行exec opcode，预期：成功
        Returns:

        """
        account = self.Ckb_cli.util_key_info_by_private_key(
            self.Config.ACCOUNT_PRIVATE_1
        )
        father_tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(
            self.Config.ACCOUNT_PRIVATE_1,
            account["address"]["testnet"],
            100000,
            self.node.getClient().url,
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
            "out_point": {
                "index": "0x0",
                "tx_hash": self.ipc_test_with_exec_contract_tx_hash,
            },
        }
        ipc_req = {
            "version": "0x0",
            "method_id": "0x0",
            "payload_format": "json",
            "payload": {
                "MathAdd": {"a": 2, "b": 1},
            },
        }
        ipc_env = {
            "tx": tx,
            "script_group_type": "lock",
            "script_hash": account["lock_hash"],
        }
        ipc_call_result = self.node.getClient().ipc_call(
            ipc_script_locator, ipc_req, ipc_env
        )
        print("ipc_call_result:", ipc_call_result)
        assert ipc_call_result["payload"]["MathAdd"] == 3

    def test_math_add_with_spawn(self):
        """
        调用合约执行 spawn opcode
        Returns:

        """
        account = self.Ckb_cli.util_key_info_by_private_key(
            self.Config.ACCOUNT_PRIVATE_1
        )
        father_tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(
            self.Config.ACCOUNT_PRIVATE_1,
            account["address"]["testnet"],
            100000,
            self.node.getClient().url,
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
                {
                    "tx_hash": self.ipc_test_with_spawn_contract_tx_hash,
                    "index_hex": hex(0),
                },
            ],
        )
        result = self.node.getClient().test_tx_pool_accept(tx, "passthrough")
        print("result:", result)
        #
        ipc_script_locator = {
            "out_point": {"index": "0x0", "tx_hash": self.ipc_test_contract_tx_hash},
        }
        ipc_req = {
            "version": "0x0",
            "method_id": "0x0",
            "payload_format": "json",
            "payload": {
                "Spawn": {"s": "Hello"},
            },
        }
        ipc_env = {
            "tx": tx,
            "script_group_type": "lock",
            "script_hash": account["lock_hash"],
        }
        ipc_call_result = self.node.getClient().ipc_call(
            ipc_script_locator, ipc_req, ipc_env
        )
        print("ipc_call_result:", ipc_call_result)
        assert ipc_call_result["payload"]["Spawn"] == "Hello"

    def test_math_add_with_hex(self):
        """
        "hex" 模式下传递有效 hex 字符串
        Returns:

        """
        ipc_script_locator = {
            "out_point": {"index": "0x0", "tx_hash": self.ipc_test_contract_tx_hash},
        }
        ipc_req = {
            "version": "0x0",
            "method_id": "0x0",
            "payload_format": "hex",
            "payload": "0x"
            + bytearray(
                json.dumps(
                    {
                        "MathAdd": {"a": 2, "b": 1},
                    }
                ).encode()
            ).hex(),
        }
        ipc_ret = self.node.getClient().ipc_call(ipc_script_locator, ipc_req)
        print(f"main: call result data={ipc_ret}")
        assert (
            json.loads(bytearray.fromhex(ipc_ret["payload"][2:]).decode())["MathAdd"]
            == 3
        )

    def test_math_add_with_xml(self):
        """
        错误的 payload_format（如 "xml"）应返回错误:unknown variant `xml`
        Returns:

        """
        ipc_script_locator = {
            "out_point": {"index": "0x0", "tx_hash": self.ipc_test_contract_tx_hash},
        }
        ipc_req = {
            "version": "0x0",
            "method_id": "0x0",
            "payload_format": "xml",
            "payload": "0x"
            + bytearray(
                json.dumps(
                    {
                        "MathAdd": {"a": 2, "b": 1},
                    }
                ).encode()
            ).hex(),
        }

        with pytest.raises(Exception) as exc_info:
            ipc_ret = self.node.getClient().ipc_call(ipc_script_locator, ipc_req)
        expected_error_message = "unknown variant `xml`"
        assert (
            expected_error_message in exc_info.value.args[0]
        ), f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

    def test_math_add_with_type_id_args(self):
        """
        存在的type script args，并且是spawn serve 合约，预期:执行成功
        Returns:

        """
        tx = self.node.getClient().get_transaction(self.ipc_test_contract_tx_hash)
        ipc_script_locator = {
            "type_id_args": tx["transaction"]["outputs"][0]["type"]["args"],
        }
        ipc_req = {
            "version": "0x0",
            "method_id": "0x0",
            "payload_format": "json",
            "payload": {
                "MathAdd": {"a": 2, "b": 1},
            },
        }
        ipc_ret = self.node.getClient().ipc_call(ipc_script_locator, ipc_req)
        print(f"main: call result json={ipc_ret}")
        assert ipc_ret["payload"]["MathAdd"] == 3

    def test_test_call_syscall_load_script(self):
        """
        syscall_load_script
        Returns:

        """
        tx = self.node.getClient().get_transaction(self.ipc_test_contract_tx_hash)
        ipc_script_locator = {
            "type_id_args": tx["transaction"]["outputs"][0]["type"]["args"],
        }

        ipc_script_locator = {
            "out_point": {"index": "0x0", "tx_hash": self.ipc_test_contract_tx_hash}
        }
        ipc_req = {
            "version": "0x0",
            "method_id": "0x0",
            "payload_format": "json",
            "payload": {
                "SyscallLoadScript": {},
            },
        }
        ipc_ret = self.node.getClient().ipc_call(ipc_script_locator, ipc_req)

        # https://explorer.nervos.org/address/ckb1qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqp29j5z9tay5gqgqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqj34x52
        assert (
            bytearray(ipc_ret["payload"]["SyscallLoadScript"]).hex()
            == "35000000100000003000000031000000b95123c71a870e3f0f74a7ee1dab8268dbfbc1407b46733ebd1b41f854b4324a0100000000"
        )

    def test_test_call_syscall_load_script_with_env(self):
        """
        syscall_load_script
        Returns:

        """
        account = self.Ckb_cli.util_key_info_by_private_key(
            self.Config.ACCOUNT_PRIVATE_1
        )
        father_tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(
            self.Config.ACCOUNT_PRIVATE_1,
            account["address"]["testnet"],
            100000,
            self.node.getClient().url,
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
                {
                    "tx_hash": self.ipc_test_with_spawn_contract_tx_hash,
                    "index_hex": hex(0),
                },
            ],
        )
        result = self.node.getClient().test_tx_pool_accept(tx, "passthrough")
        print("result:", result)
        #
        ipc_script_locator = {
            "out_point": {"index": "0x0", "tx_hash": self.ipc_test_contract_tx_hash},
        }
        ipc_req = {
            "version": "0x0",
            "method_id": "0x0",
            "payload_format": "json",
            "payload": {
                "SyscallLoadScript": {},
            },
        }
        ipc_env = {
            "tx": tx,
            "script_group_type": "lock",
            "script_hash": account["lock_hash"],
        }
        ipc_call_result = self.node.getClient().ipc_call(
            ipc_script_locator, ipc_req, ipc_env
        )
        assert (
            f"490000001000000030000000310000009bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce80114000000{account['lock_arg'][2:]}"
            == bytearray(ipc_call_result["payload"]["SyscallLoadScript"]).hex()
        )

    def test_type_id_args_not_exist(self):
        """
         不存在的type script args，预期：执行失败
        Returns:
        """
        ipc_script_locator = {
            "type_id_args": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
        }
        ipc_req = {
            "version": "0x0",
            "method_id": "0x0",
            "payload_format": "json",
            "payload": {
                "MathAdd": {"a": 2, "b": 1},
            },
        }

        with pytest.raises(Exception) as exc_info:
            ipc_ret = self.node.getClient().ipc_call(ipc_script_locator, ipc_req)
        # todo add expected_error_message
        expected_error_message = "Get type id args failed"
        assert (
            expected_error_message in exc_info.value.args[0]
        ), f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

    def test_mix_payload(self):
        """
        复杂 payload，含多层嵌套的结构或大数据，预期：成功
        Returns:

        """
        # deploy math contract
        test_vec = [
            {
                "bool_data": True,
                "char_data": "0",
                "f32_data": 3.4028235,
                "f64_data": 1.7976931348623157,
                "i128_data": 17014118346046923,
                "i16_data": 32767,
                "i32_data": 2147483647,
                "i64_data": 9223372036854775807,
                "i8_data": 127,
                "isize_data": 0,
                "str_data": "max",
                "u128_data": 3402823669209385,
                "u16_data": 65535,
                "u32_data": 4294967295,
                "u64_data": 18446744073709551615,
                "u8_data": 255,
                "usize_data": 18446744073709551615,
            },
            {
                "bool_data": False,
                "char_data": " ",
                "f32_data": -3.4028235,
                "f64_data": -1.7976931348623157,
                "i128_data": -17014118346046923,
                "i16_data": -32768,
                "i32_data": -2147483648,
                "i64_data": -9223372036854775808,
                "i8_data": -128,
                "isize_data": -9223372036854775808,
                "str_data": "",
                "u128_data": 0,
                "u16_data": 0,
                "u32_data": 0,
                "u64_data": 0,
                "u8_data": 0,
                "usize_data": 0,
            },
        ]
        ipc_script_locator = {
            "out_point": {"index": "0x0", "tx_hash": self.ipc_test_contract_tx_hash}
        }
        ipc_req = {
            "version": "0x0",
            "method_id": "0x0",
            "payload_format": "json",
            "payload": {
                "TestBoundaryStruct": {"vec": test_vec},
            },
        }
        ipc_ret = self.node.getClient().ipc_call(ipc_script_locator, ipc_req)
        print(f"main: call result json={ipc_ret}")
        assert (
            json.dumps(ipc_ret["payload"])
            == '{"TestBoundaryStruct": [{"bool_data": true, "char_data": "0", "f32_data": 3.4028234, "f64_data": 1.7976931348623155, "i128_data": 17014118346046923, "i16_data": 32767, "i32_data": 2147483647, "i64_data": 9223372036854775807, "i8_data": 127, "isize_data": 0, "str_data": "max", "u128_data": 3402823669209385, "u16_data": 65535, "u32_data": 4294967295, "u64_data": 18446744073709551615, "u8_data": 255, "usize_data": 18446744073709551615}, {"bool_data": false, "char_data": " ", "f32_data": -3.4028234, "f64_data": -1.7976931348623155, "i128_data": -17014118346046923, "i16_data": -32768, "i32_data": -2147483648, "i64_data": -9223372036854775808, "i8_data": -128, "isize_data": -9223372036854775808, "str_data": "", "u128_data": 0, "u16_data": 0, "u32_data": 0, "u64_data": 0, "u8_data": 0, "usize_data": 0}]}'
        )

    def test_script_group_type_type(self):
        """
        type合约 ，预期：成功
        不存在匹配的script_hash，预期：报错 IPC: ScriptNotFound
        已经上过链的tx，预期：报错：TransactionFailedToResolve
        Returns:

        """
        account = self.Ckb_cli.util_key_info_by_private_key(
            self.Config.ACCOUNT_PRIVATE_1
        )
        account1 = self.Ckb_cli.util_key_info_by_private_key(
            self.Config.ACCOUNT_PRIVATE_2
        )
        account2 = self.Ckb_cli.util_key_info_by_private_key(
            self.Config.MINER_PRIVATE_1
        )

        # deploy
        udtContract = UdtContract()
        udtContract.deploy(self.Config.ACCOUNT_PRIVATE_1, self.node)
        deploy_hash, deploy_index = udtContract.get_deploy_hash_and_index()
        # issue
        invoke_arg, invoke_data = udtContract.issue(account1["lock_arg"], 100000)
        tx_hash = self.Contract.invoke_ckb_contract(
            account_private=self.Config.ACCOUNT_PRIVATE_2,
            contract_out_point_tx_hash=deploy_hash,
            contract_out_point_tx_index=deploy_index,
            type_script_arg=invoke_arg,
            hash_type="type",
            data=invoke_data,
            fee=1000,
            api_url=self.node.getClient().url,
            cell_deps=[],
            input_cells=[],
            output_lock_arg=account2["lock_arg"],
        )
        tx = self.node.getClient().get_transaction(tx_hash)

        print("tx:", tx)
        molecule_hex = self.Ckb_cli.molecule_encode(
            tx["transaction"]["outputs"][0]["type"], "Script"
        )
        data = bytes.fromhex(molecule_hex.replace("0x", ""))
        personalization = "ckb-default-hash".encode("utf-8")
        # cal blake 2b hash
        hash_object = hashlib.blake2b(digest_size=32, person=personalization)
        hash_object.update(data)
        script_hash = "0x" + hash_object.hexdigest()
        print("hex:", script_hash)
        tx = tx["transaction"]
        del tx["hash"]
        ipc_script_locator = {
            "out_point": {"index": "0x0", "tx_hash": self.ipc_test_contract_tx_hash},
        }
        ipc_req = {
            "version": "0x0",
            "method_id": "0x0",
            "payload_format": "json",
            "payload": {
                "SyscallLoadScript": {},
            },
        }
        ipc_env = {
            "tx": tx,
            "script_group_type": "type",
            "script_hash": script_hash,
        }
        ipc_call_result = self.node.getClient().ipc_call(
            ipc_script_locator, ipc_req, ipc_env
        )
        print("ipc_call_result:", ipc_call_result)

        # 不匹配hash
        ipc_env["script_hash"] = (
            "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8"
        )

        # ScriptNotFound
        with pytest.raises(Exception) as exc_info:
            ipc_call_result = self.node.getClient().ipc_call(
                ipc_script_locator, ipc_req, ipc_env
            )
        expected_error_message = "ScriptNotFound"
        assert (
            expected_error_message in exc_info.value.args[0]
        ), f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

        self.Miner.miner_until_tx_committed(self.node, tx_hash)

        with pytest.raises(Exception) as exc_info:
            self.node.getClient().ipc_call(ipc_script_locator, ipc_req, ipc_env)
        expected_error_message = "TransactionFailedToResolve: Unknown(OutPoint"
        assert (
            expected_error_message in exc_info.value.args[0]
        ), f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

    def test_script_is_data_data1_data2(self):
        """
        tx的script 是data
        tx的script 是data1
        tx的script 是data2
        Returns:

        """

        account1 = self.Ckb_cli.util_key_info_by_private_key(
            self.Config.MINER_PRIVATE_1
        )

        # deploy
        udtContract = UdtContract()
        udtContract.deploy(self.Config.ACCOUNT_PRIVATE_1, self.node)
        deploy_hash, deploy_index = udtContract.get_deploy_hash_and_index()
        # data
        invoke_arg, invoke_data = udtContract.issue(account1["lock_arg"], 100000)
        tx = self.Contract.build_invoke_ckb_contract(
            account_private=self.Config.MINER_PRIVATE_1,
            contract_out_point_tx_hash=deploy_hash,
            contract_out_point_tx_index=deploy_index,
            type_script_arg=invoke_arg,
            hash_type="data",
            data=invoke_data,
            fee=1000,
            api_url=self.node.getClient().url,
        )

        print("tx:", tx)
        molecule_hex = self.Ckb_cli.molecule_encode(tx["outputs"][0]["type"], "Script")
        data = bytes.fromhex(molecule_hex.replace("0x", ""))
        personalization = "ckb-default-hash".encode("utf-8")
        # cal blake 2b hash
        hash_object = hashlib.blake2b(digest_size=32, person=personalization)
        hash_object.update(data)
        script_hash = "0x" + hash_object.hexdigest()
        print("hex:", script_hash)
        # tx = tx["transaction"]
        # del tx["hash"]
        ipc_script_locator = {
            "out_point": {"index": "0x0", "tx_hash": self.ipc_test_contract_tx_hash},
        }
        ipc_req = {
            "version": "0x0",
            "method_id": "0x0",
            "payload_format": "json",
            "payload": {
                "SyscallLoadScript": {},
            },
        }
        ipc_env = {
            "tx": tx,
            "script_group_type": "type",
            "script_hash": script_hash,
        }

        with pytest.raises(Exception) as exc_info:
            ipc_call_result = self.node.getClient().ipc_call(
                ipc_script_locator, ipc_req, ipc_env
            )
        expected_error_message = "IPC: sending on a closed channel"
        assert (
            expected_error_message in exc_info.value.args[0]
        ), f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

        # data1
        invoke_arg, invoke_data = udtContract.issue(account1["lock_arg"], 100000)
        tx = self.Contract.build_invoke_ckb_contract(
            account_private=self.Config.MINER_PRIVATE_1,
            contract_out_point_tx_hash=deploy_hash,
            contract_out_point_tx_index=deploy_index,
            type_script_arg=invoke_arg,
            hash_type="data1",
            data=invoke_data,
            fee=1000,
            api_url=self.node.getClient().url,
        )

        molecule_hex = self.Ckb_cli.molecule_encode(tx["outputs"][0]["type"], "Script")
        data = bytes.fromhex(molecule_hex.replace("0x", ""))
        personalization = "ckb-default-hash".encode("utf-8")
        # cal blake 2b hash
        hash_object = hashlib.blake2b(digest_size=32, person=personalization)
        hash_object.update(data)
        script_hash = "0x" + hash_object.hexdigest()
        print("hex:", script_hash)
        # tx = tx["transaction"]
        # del tx["hash"]
        ipc_script_locator = {
            "out_point": {"index": "0x0", "tx_hash": self.ipc_test_contract_tx_hash},
        }
        ipc_req = {
            "version": "0x0",
            "method_id": "0x0",
            "payload_format": "json",
            "payload": {
                "SyscallLoadScript": {},
            },
        }
        ipc_env = {
            "tx": tx,
            "script_group_type": "type",
            "script_hash": script_hash,
        }
        ipc_call_result = self.node.getClient().ipc_call(
            ipc_script_locator, ipc_req, ipc_env
        )

        # data2
        invoke_arg, invoke_data = udtContract.issue(account1["lock_arg"], 100000)
        tx = self.Contract.build_invoke_ckb_contract(
            account_private=self.Config.MINER_PRIVATE_1,
            contract_out_point_tx_hash=deploy_hash,
            contract_out_point_tx_index=deploy_index,
            type_script_arg=invoke_arg,
            hash_type="data2",
            data=invoke_data,
            fee=1000,
            api_url=self.node.getClient().url,
        )

        print("tx:", tx)
        molecule_hex = self.Ckb_cli.molecule_encode(tx["outputs"][0]["type"], "Script")
        data = bytes.fromhex(molecule_hex.replace("0x", ""))
        personalization = "ckb-default-hash".encode("utf-8")
        # cal blake 2b hash
        hash_object = hashlib.blake2b(digest_size=32, person=personalization)
        hash_object.update(data)
        script_hash = "0x" + hash_object.hexdigest()
        print("hex:", script_hash)
        # tx = tx["transaction"]
        # del tx["hash"]
        ipc_script_locator = {
            "out_point": {"index": "0x0", "tx_hash": self.ipc_test_contract_tx_hash},
        }
        ipc_req = {
            "version": "0x0",
            "method_id": "0x0",
            "payload_format": "json",
            "payload": {
                "SyscallLoadScript": {},
            },
        }
        ipc_env = {
            "tx": tx,
            "script_group_type": "type",
            "script_hash": script_hash,
        }
        ipc_call_result = self.node.getClient().ipc_call(
            ipc_script_locator, ipc_req, ipc_env
        )

    def test_cycle_limit(self):
        """
        cycle执行特别大，测试cycle 请求最大值100亿，超过100亿，报错：IPC: ReadVlqError
        Returns:
        """
        # deploy math contract
        ipc_script_locator = {
            "out_point": {"index": "0x0", "tx_hash": self.ipc_test_contract_tx_hash}
        }
        ipc_req = {
            "version": "0x0",
            "method_id": "0x0",
            "payload_format": "json",
            "payload": {
                "TestCycle": {"cycle_limit": 9999994700},
            },
        }
        ipc_ret = self.node.getClient().ipc_call(ipc_script_locator, ipc_req)
        print(f"main: call result json={ipc_ret}")
        assert ipc_ret["payload"]["TestCycle"] > 9999994700
        ipc_req = {
            "version": "0x0",
            "method_id": "0x0",
            "payload_format": "json",
            "payload": {
                "TestCycle": {"cycle_limit": 10000000000},
            },
        }

        with pytest.raises(Exception) as exc_info:
            ipc_ret = self.node.getClient().ipc_call(ipc_script_locator, ipc_req)
        expected_error_message = "IPC: ReadVlqError"
        assert (
            expected_error_message in exc_info.value.args[0]
        ), f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

    def test_payload_limit(self):
        """
        测试返回payload 最大值,请求小于64k，成功，超过64k ，报错：：IPC: ReadVlqError
        Returns:

        """
        # deploy math contract
        ipc_script_locator = {
            "out_point": {"index": "0x0", "tx_hash": self.ipc_test_contract_tx_hash}
        }
        ipc_req = {
            "version": "0x0",
            "method_id": "0x0",
            "payload_format": "json",
            "payload": {
                "TestMem": {"byte_data": 1000, "kb_data": 63, "mb_data": 0},
            },
        }
        ipc_ret = self.node.getClient().ipc_call(ipc_script_locator, ipc_req)
        print(f"main: call result json={ipc_ret}")
        assert len(ipc_ret["payload"]["TestMem"]) == 1000 + 63 * 1024

        ipc_req = {
            "version": "0x0",
            "method_id": "0x0",
            "payload_format": "json",
            "payload": {
                "TestMem": {"byte_data": 0, "kb_data": 64, "mb_data": 0},
            },
        }

        with pytest.raises(Exception) as exc_info:
            ipc_ret = self.node.getClient().ipc_call(ipc_script_locator, ipc_req)
        expected_error_message = "IPC: ReadVlqError"
        assert (
            expected_error_message in exc_info.value.args[0]
        ), f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

    def test_input_payload(self):
        """
        payload 请求特别大，测试payload 请求最大值,如果是str 128*1024 ，vec 1024 * 64  就会报错：IPC: ReadVlqError~~

        Returns:

        """
        ipc_script_locator = {
            "out_point": {"index": "0x0", "tx_hash": self.ipc_test_contract_tx_hash}
        }
        ipc_req = {
            "version": "0x0",
            "method_id": "0x0",
            "payload_format": "json",
            "payload": {
                "TestInputPayload": {"s": rand_str(1024 * 128)},
            },
        }
        ipc_ret = self.node.getClient().ipc_call(ipc_script_locator, ipc_req)
        print(f"main: call result json={ipc_ret}")

        ipc_req = {
            "version": "0x0",
            "method_id": "0x0",
            "payload_format": "json",
            "payload": {
                "TestInputPayload": {"s": rand_str(1024 * 129)},
            },
        }
        with pytest.raises(Exception) as exc_info:
            ipc_ret = self.node.getClient().ipc_call(ipc_script_locator, ipc_req)
        expected_error_message = "IPC: ReadVlqError"
        assert (
            expected_error_message in exc_info.value.args[0]
        ), f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

        ipc_req = {
            "version": "0x0",
            "method_id": "0x0",
            "payload_format": "json",
            "payload": {
                "TestInputVec": {"vec": [1] * 1024 * 64},
            },
        }
        ipc_ret = self.node.getClient().ipc_call(ipc_script_locator, ipc_req)
        assert ipc_ret["payload"]["TestInputVec"] == 1024 * 64

        ipc_req = {
            "version": "0x0",
            "method_id": "0x0",
            "payload_format": "json",
            "payload": {
                "TestInputVec": {"vec": [1] * 1024 * 65},
            },
        }
        with pytest.raises(Exception) as exc_info:
            ipc_ret = self.node.getClient().ipc_call(ipc_script_locator, ipc_req)
        expected_error_message = "IPC: ReadVlqError"
        assert (
            expected_error_message in exc_info.value.args[0]
        ), f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

    def test_ckb_opcode(self):
        """
        有IpcEnv 测试所有的block 操作是否能正常使用
            调用查询 opcode

        没有IpcEnv 测试所有的block 操作是否能正常使用
            调用查询opcode, current_cycle,load 一些查询会失败，报错：返回
        Returns:

        """
        account1 = self.Ckb_cli.util_key_info_by_private_key(
            self.Config.MINER_PRIVATE_1
        )
        # deploy
        udtContract = UdtContract()
        udtContract.deploy(self.Config.ACCOUNT_PRIVATE_1, self.node)
        deploy_hash, deploy_index = udtContract.get_deploy_hash_and_index()
        # data
        invoke_arg, invoke_data = udtContract.issue(account1["lock_arg"], 100000)
        tx = self.Contract.build_invoke_ckb_contract(
            account_private=self.Config.MINER_PRIVATE_1,
            contract_out_point_tx_hash=deploy_hash,
            contract_out_point_tx_index=deploy_index,
            type_script_arg=invoke_arg,
            hash_type="type",
            data=invoke_data,
            fee=1000,
            api_url=self.node.getClient().url,
        )

        print("tx:", tx)
        molecule_hex = self.Ckb_cli.molecule_encode(tx["outputs"][0]["type"], "Script")
        data = bytes.fromhex(molecule_hex.replace("0x", ""))
        personalization = "ckb-default-hash".encode("utf-8")
        # cal blake 2b hash
        hash_object = hashlib.blake2b(digest_size=32, person=personalization)
        hash_object.update(data)
        script_hash = "0x" + hash_object.hexdigest()
        print("hex:", script_hash)
        # tx = tx["transaction"]
        # del tx["hash"]
        ipc_script_locator = {
            "out_point": {"index": "0x0", "tx_hash": self.ipc_test_contract_tx_hash},
        }
        ipc_req = {
            "version": "0x0",
            "method_id": "0x0",
            "payload_format": "json",
            "payload": {
                "TestCkbCall": {},
            },
        }
        ipc_env = {
            "tx": tx,
            "script_group_type": "type",
            "script_hash": script_hash,
        }

        ipc_call_result = self.node.getClient().ipc_call(
            ipc_script_locator, ipc_req, ipc_env
        )

        with pytest.raises(Exception) as exc_info:
            ipc_call_result = self.node.getClient().ipc_call(
                ipc_script_locator, ipc_req, None
            )
        expected_error_message = "IPC: ReadVlqError"
        assert (
            expected_error_message in exc_info.value.args[0]
        ), f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

    def test_empty(self):
        """

        Returns:

        """
        tx = self.node.getClient().get_transaction(self.ipc_test_contract_tx_hash)
        ipc_script_locator = {
            "type_id_args": tx["transaction"]["outputs"][0]["type"]["args"],
        }
        ipc_req = {
            "version": "0x0",
            "method_id": "0x0",
            "payload_format": "json",
            "payload": {
                "TestEmpty": {},
            },
        }
        ipc_ret = self.node.getClient().ipc_call(ipc_script_locator, ipc_req)
        print(f"main: call result json={ipc_ret}")
        assert ipc_ret["payload"]["TestEmpty"] == None

    def test_ipc_time_with_exec(self):
        """
        死循环，执行时间超过8s,预期：rpc返回sending on a closed channel,vm 继续执行
        Returns:

        """
        account = self.Ckb_cli.util_key_info_by_private_key(
            self.Config.ACCOUNT_PRIVATE_1
        )
        father_tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(
            self.Config.ACCOUNT_PRIVATE_1,
            account["address"]["testnet"],
            100000,
            self.node.getClient().url,
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
                {
                    "tx_hash": self.ipc_test_with_exec_contract_tx_hash,
                    "index_hex": hex(0),
                },
            ],
        )
        result = self.node.getClient().test_tx_pool_accept(tx, "passthrough")
        print("result:", result)
        #
        ipc_script_locator = {
            "out_point": {
                "index": "0x0",
                "tx_hash": self.ipc_test_with_exec_contract_tx_hash,
            },
        }
        ipc_req = {
            "version": "0x0",
            "method_id": "0x0",
            "payload_format": "json",
            "payload": {
                "TestCurrentCycle": {},
            },
        }
        ipc_env = {
            "tx": tx,
            "script_group_type": "lock",
            "script_hash": account["lock_hash"],
        }

        # IPC: sending on a closed channel
        with pytest.raises(Exception) as exc_info:
            ipc_call_result = self.node.getClient().ipc_call(
                ipc_script_locator, ipc_req, ipc_env
            )
        expected_error_message = "sending on a closed channel"
        assert (
            expected_error_message in exc_info.value.args[0]
        ), f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"


def rand_str(size):
    """
    生成随机字符串
    :param size: 字符串长度
    :return: 随机字符串
    """
    return "".join(random.choice(string.ascii_letters) for _ in range(size))
