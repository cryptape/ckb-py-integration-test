import time

import pytest

from framework.basic import CkbTest
from framework.helper.spawn_arg import SpawnArgContract
from framework.util import get_project_root


class MemoryLimitTest(CkbTest):

    @classmethod
    def setup_class(cls):
        cls.node = cls.CkbNode.init_dev_by_port(
            cls.CkbNodeConfigPath.CURRENT_TEST, "contract/node1", 8116, 8115
        )
        cls.node119 = cls.CkbNode.init_dev_by_port(
            cls.CkbNodeConfigPath.v120, "contract/node2", 8117, 8118
        )

        cls.node119.prepare()
        cls.node119.start()
        cls.node.prepare()
        cls.node.start()

        cls.Miner.make_tip_height_number(cls.node, 2000)
        cls.node.getClient().generate_epochs("0x2")
        cls.node119.connected(cls.node)
        cls.spawnArgContract = SpawnArgContract()
        cls.spawnArgContract.deploy(cls.Config.ACCOUNT_PRIVATE_1, cls.node)
        deploy_hash, deploy_index = cls.spawnArgContract.get_deploy_hash_and_index()
        print("deploy_hash:", deploy_hash)
        print("deploy_index:", deploy_index)
        tip_number = cls.node.getClient().get_tip_block_number()
        cls.Node.wait_node_height(cls.node119, tip_number, 100000)
        # cls.spawnArgContract = SpawnArgContract("0x202222df23f05c3c1d11b24b1e4757877480a1b2c1631c4e0fdc5f38d4625de9", 0)

    @classmethod
    def teardown_class(cls):
        cls.node.stop()
        cls.node.clean()
        cls.node119.stop()
        cls.node119.clean()
        # pass

    def test_spawn(self):
        with pytest.raises(Exception) as exc_info:
            self.deploy_and_invoke(
                self.Config.ACCOUNT_PRIVATE_1,
                f"{get_project_root()}/source/contract/test_cases/spawn_oom",
                self.node,
            )
        # expected_error_message = "@@@VM@@@UNEXPECTED@@@ARGV@@@TOOLONG@@@"
        expected_error_message = "MemOutOfStack"
        assert expected_error_message in exc_info.value.args[0], (
            f"Expected substring '{expected_error_message}' "
            f"not found in actual string '{exc_info.value.args[0]}'"
        )

    def test_oom(self):
        account2 = self.Ckb_cli.util_key_info_by_private_key(
            self.Config.MINER_PRIVATE_1
        )
        deploy_hash, deploy_index = self.spawnArgContract.get_deploy_hash_and_index()

        # oom
        with pytest.raises(Exception) as exc_info:
            invoke_arg, invoke_data = self.spawnArgContract.get_test_data(
                1024 * 8 * 2, 0, 0
            )
            tx_hash = self.Contract.invoke_ckb_contract(
                account_private=self.Config.MINER_PRIVATE_1,
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
        # expected_error_message = "@@@VM@@@UNEXPECTED@@@ARGV@@@TOOLONG@@@"
        expected_error_message = "MemOutOfStack"
        assert expected_error_message in exc_info.value.args[0], (
            f"Expected substring '{expected_error_message}' "
            f"not found in actual string '{exc_info.value.args[0]}'"
        )

    def test_MemOutOfStack(self):
        account2 = self.Ckb_cli.util_key_info_by_private_key(
            self.Config.MINER_PRIVATE_1
        )
        deploy_hash, deploy_index = self.spawnArgContract.get_deploy_hash_and_index()

        # 合法交易边界
        invoke_arg, invoke_data = self.spawnArgContract.get_test_data(0, 1013, 111)
        tx_hash = self.Contract.invoke_ckb_contract(
            account_private=self.Config.MINER_PRIVATE_1,
            contract_out_point_tx_hash=deploy_hash,
            contract_out_point_tx_index=deploy_index,
            type_script_arg=invoke_arg,
            hash_type="type",
            data=invoke_data,
            fee=1000,
            api_url=self.node119.getClient().url,
            cell_deps=[],
            input_cells=[],
            output_lock_arg=account2["lock_arg"],
        )
        print(tx_hash)
        self.Miner.miner_until_tx_committed(self.node119, tx_hash)
        tip_number = self.node.getClient().get_tip_block_number()
        self.Node.wait_node_height(self.node, tip_number, 100000)

        # MemOutOfStack 边界  119
        invoke_arg, invoke_data = self.spawnArgContract.get_test_data(0, 1013, 112)
        with pytest.raises(Exception) as exc_info:
            tx_hash = self.Contract.invoke_ckb_contract(
                account_private=self.Config.MINER_PRIVATE_1,
                contract_out_point_tx_hash=deploy_hash,
                contract_out_point_tx_index=deploy_index,
                type_script_arg=invoke_arg,
                hash_type="type",
                data=invoke_data,
                fee=1000,
                api_url=self.node119.getClient().url,
                cell_deps=[],
                input_cells=[],
                output_lock_arg=account2["lock_arg"],
            )
        expected_error_message = "MemOutOfStack"
        assert expected_error_message in exc_info.value.args[0], (
            f"Expected substring '{expected_error_message}' "
            f"not found in actual string '{exc_info.value.args[0]}'"
        )

        # MemOutOfStack 120
        with pytest.raises(Exception) as exc_info:
            tx_hash = self.Contract.invoke_ckb_contract(
                account_private=self.Config.MINER_PRIVATE_1,
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
        expected_error_message = "MemOutOfStack"
        assert expected_error_message in exc_info.value.args[0], (
            f"Expected substring '{expected_error_message}' "
            f"not found in actual string '{exc_info.value.args[0]}'"
        )

        with pytest.raises(Exception) as exc_info:
            invoke_arg, invoke_data = self.spawnArgContract.get_test_data(
                3, 895 + 32, 92
            )
            tx_hash = self.Contract.invoke_ckb_contract(
                account_private=self.Config.MINER_PRIVATE_1,
                contract_out_point_tx_hash=deploy_hash,
                contract_out_point_tx_index=deploy_index,
                type_script_arg=invoke_arg,
                hash_type="type",
                data=invoke_data,
                fee=1000,
                api_url=self.node119.getClient().url,
                cell_deps=[],
                input_cells=[],
                output_lock_arg=account2["lock_arg"],
            )
            # self.node.getClient().test_tx_pool_accept(tx,"passthrough")
            self.Miner.miner_until_tx_committed(self.node119, tx_hash)
        expected_error_message = "MemOutOfStack"
        assert expected_error_message in exc_info.value.args[0], (
            f"Expected substring '{expected_error_message}' "
            f"not found in actual string '{exc_info.value.args[0]}'"
        )

        with pytest.raises(Exception) as exc_info:
            invoke_arg, invoke_data = self.spawnArgContract.get_test_data(
                3, 895 + 32, 92
            )
            tx_hash = self.Contract.invoke_ckb_contract(
                account_private=self.Config.MINER_PRIVATE_1,
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
            # self.node.getClient().test_tx_pool_accept(tx,"passthrough")
            self.Miner.miner_until_tx_committed(self.node119, tx_hash)
        # expected_error_message = "@@@VM@@@UNEXPECTED@@@ARGV@@@TOOLONG@@@"
        expected_error_message = "MemOutOfStack"
        assert expected_error_message in exc_info.value.args[0], (
            f"Expected substring '{expected_error_message}' "
            f"not found in actual string '{exc_info.value.args[0]}'"
        )

    def test_bug(self):
        """
        不一致bug
            mb_size:3
            kb_size:9949
            byte_size:2336
            改动分支执行 执行成功
            120分支:MemWriteOnExecutablePage
        Returns:
        """
        account2 = self.Ckb_cli.util_key_info_by_private_key(
            self.Config.MINER_PRIVATE_1
        )
        deploy_hash, deploy_index = self.spawnArgContract.get_deploy_hash_and_index()
        with pytest.raises(Exception) as exc_info:
            invoke_arg, invoke_data = self.spawnArgContract.get_test_data(
                3, 9949, 2300 + 36
            )
            tx_hash = self.Contract.invoke_ckb_contract(
                account_private=self.Config.MINER_PRIVATE_1,
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
        expected_error_message = "MemOutOfStack"
        # expected_error_message = "@@@VM@@@UNEXPECTED@@@ARGV@@@TOOLONG@@@"
        assert expected_error_message in exc_info.value.args[0], (
            f"Expected substring '{expected_error_message}' "
            f"not found in actual string '{exc_info.value.args[0]}'"
        )

    def test_MemWriteOnExecutablePage(self):
        self.Miner.miner_with_version(self.node, "0x0")
        account2 = self.Ckb_cli.util_key_info_by_private_key(
            self.Config.MINER_PRIVATE_1
        )
        deploy_hash, deploy_index = self.spawnArgContract.get_deploy_hash_and_index()

        with pytest.raises(Exception) as exc_info:
            invoke_arg, invoke_data = self.spawnArgContract.get_test_data(
                3, 895 + 32, 93
            )
            tx_hash = self.Contract.invoke_ckb_contract(
                account_private=self.Config.MINER_PRIVATE_1,
                contract_out_point_tx_hash=deploy_hash,
                contract_out_point_tx_index=deploy_index,
                type_script_arg=invoke_arg,
                hash_type="type",
                data=invoke_data,
                fee=1000,
                api_url=self.node119.getClient().url,
                cell_deps=[],
                input_cells=[],
                output_lock_arg=account2["lock_arg"],
            )
            # self.node.getClient().test_tx_pool_accept(tx,"passthrough")
            self.Miner.miner_until_tx_committed(self.node119, tx_hash)
        expected_error_message = "MemWriteOnExecutablePage"
        assert expected_error_message in exc_info.value.args[0], (
            f"Expected substring '{expected_error_message}' "
            f"not found in actual string '{exc_info.value.args[0]}'"
        )

        with pytest.raises(Exception) as exc_info:
            invoke_arg, invoke_data = self.spawnArgContract.get_test_data(
                3, 895 + 32, 93
            )
            tx_hash = self.Contract.invoke_ckb_contract(
                account_private=self.Config.MINER_PRIVATE_1,
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
            # self.node.getClient().test_tx_pool_accept(tx,"passthrough")
            self.Miner.miner_until_tx_committed(self.node119, tx_hash)
        # expected_error_message = "@@@VM@@@UNEXPECTED@@@ARGV@@@TOOLONG@@@"
        expected_error_message = "MemOutOfStack"
        assert expected_error_message in exc_info.value.args[0], (
            f"Expected substring '{expected_error_message}' "
            f"not found in actual string '{exc_info.value.args[0]}'"
        )

        with pytest.raises(Exception) as exc_info:
            invoke_arg, invoke_data = self.spawnArgContract.get_test_data(
                3, 9949, 2300 + 36
            )
            tx_hash = self.Contract.invoke_ckb_contract(
                account_private=self.Config.MINER_PRIVATE_1,
                contract_out_point_tx_hash=deploy_hash,
                contract_out_point_tx_index=deploy_index,
                type_script_arg=invoke_arg,
                hash_type="type",
                data=invoke_data,
                fee=1000,
                api_url=self.node119.getClient().url,
                cell_deps=[],
                input_cells=[],
                output_lock_arg=account2["lock_arg"],
            )
            # self.node.getClient().test_tx_pool_accept(tx,"passthrough")
            self.Miner.miner_until_tx_committed(self.node119, tx_hash)
        expected_error_message = "MemWriteOnExecutablePage"
        assert expected_error_message in exc_info.value.args[0], (
            f"Expected substring '{expected_error_message}' "
            f"not found in actual string '{exc_info.value.args[0]}'"
        )

        with pytest.raises(Exception) as exc_info:
            invoke_arg, invoke_data = self.spawnArgContract.get_test_data(
                3, 9949, 2300 + 36
            )
            tx_hash = self.Contract.invoke_ckb_contract(
                account_private=self.Config.MINER_PRIVATE_1,
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
        # expected_error_message = "@@@VM@@@UNEXPECTED@@@ARGV@@@TOOLONG@@@"
        expected_error_message = "MemOutOfStack"
        assert expected_error_message in exc_info.value.args[0], (
            f"Expected substring '{expected_error_message}' "
            f"not found in actual string '{exc_info.value.args[0]}'"
        )

    def test_MemOutOfBound(self):
        account2 = self.Ckb_cli.util_key_info_by_private_key(
            self.Config.MINER_PRIVATE_1
        )
        deploy_hash, deploy_index = self.spawnArgContract.get_deploy_hash_and_index()

        with pytest.raises(Exception) as exc_info:
            invoke_arg, invoke_data = self.spawnArgContract.get_test_data(4, 0, 0)
            print("deploy_hash:", deploy_hash)
            tx_hash = self.Contract.invoke_ckb_contract(
                account_private=self.Config.MINER_PRIVATE_1,
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
        expected_error_message = "MemOutOfStack"
        # expected_error_message = "@@@VM@@@UNEXPECTED@@@ARGV@@@TOOLONG@@@"
        assert expected_error_message in exc_info.value.args[0], (
            f"Expected substring '{expected_error_message}' "
            f"not found in actual string '{exc_info.value.args[0]}'"
        )

        with pytest.raises(Exception) as exc_info:
            invoke_arg, invoke_data = self.spawnArgContract.get_test_data(4, 0, 0)
            print("deploy_hash:", deploy_hash)
            tx_hash = self.Contract.invoke_ckb_contract(
                account_private=self.Config.MINER_PRIVATE_1,
                contract_out_point_tx_hash=deploy_hash,
                contract_out_point_tx_index=deploy_index,
                type_script_arg=invoke_arg,
                hash_type="type",
                data=invoke_data,
                fee=1000,
                api_url=self.node119.getClient().url,
                cell_deps=[],
                input_cells=[],
                output_lock_arg=account2["lock_arg"],
            )
        expected_error_message = "MemOutOfBound"
        assert expected_error_message in exc_info.value.args[0], (
            f"Expected substring '{expected_error_message}' "
            f"not found in actual string '{exc_info.value.args[0]}'"
        )

    def test_argv_limit(self):
        account2 = self.Ckb_cli.util_key_info_by_private_key(
            self.Config.ACCOUNT_PRIVATE_2
        )
        deploy_hash, deploy_index = self.spawnArgContract.get_deploy_hash_and_index()
        invoke_arg, invoke_data = self.spawnArgContract.get_test_data(0, 1014, 8)
        print("deploy_hash:", deploy_hash)
        tx_hash = self.Contract.invoke_ckb_contract(
            account_private=self.Config.MINER_PRIVATE_1,
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
        self.Miner.miner_until_tx_committed(self.node, tx_hash)

        with pytest.raises(Exception) as exc_info:
            invoke_arg, invoke_data = self.spawnArgContract.get_test_data(0, 1014, 9)
            print("deploy_hash:", deploy_hash)
            tx_hash = self.Contract.invoke_ckb_contract(
                account_private=self.Config.MINER_PRIVATE_1,
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
            self.Miner.miner_until_tx_committed(self.node, tx_hash)

        expected_error_message = "MemOutOfStack"
        assert expected_error_message in exc_info.value.args[0], (
            f"Expected substring '{expected_error_message}' "
            f"not found in actual string '{exc_info.value.args[0]}'"
        )

    def deploy_and_invoke(self, account, path, node, try_count=5):
        if try_count < 0:
            raise Exception("try out of times")
        try:
            deploy_hash = self.Contract.deploy_ckb_contract(
                account, path, enable_type_id=True, api_url=node.getClient().url
            )
            self.Miner.miner_until_tx_committed(node, deploy_hash)
            time.sleep(1)
            beginTime = time.time()
            invoke_hash = self.Contract.invoke_ckb_contract(
                account_private=account,
                contract_out_point_tx_hash=deploy_hash,
                contract_out_point_tx_index=0,
                type_script_arg="0x02",
                data="0x1234",
                hash_type="type",
                api_url=node.getClient().url,
            )
            cost_time = time.time() - beginTime
            print("cost_time:", cost_time)
            tx = node.getClient().get_transaction(invoke_hash)
            del tx["transaction"]["hash"]
            self.node.getClient().clear_tx_pool()
            beginTime = time.time()
            self.node.getClient().test_tx_pool_accept(tx["transaction"], "passthrough")
            cost_time = time.time() - beginTime
            print("test_tx_pool_accept cost_time:", cost_time)
            return invoke_hash
        except Exception as e:
            print(e)
            if "Resolve failed Dead" in str(e):
                try_count -= 1
                for i in range(2):
                    self.Miner.miner_with_version(node, "0x0")
                time.sleep(3)
                return self.deploy_and_invoke(account, path, node, try_count)
            if "PoolRejectedRBF" in str(e):
                try_count -= 1
                for i in range(2):
                    self.Miner.miner_with_version(node, "0x0")
                time.sleep(3)
                return self.deploy_and_invoke(account, path, node, try_count)
            raise e
