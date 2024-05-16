import json

from framework.basic import CkbTest


class TestCkbCliRpc114(CkbTest):

    @classmethod
    def setup_class(cls):
        """
        1. start 1 ckb node in tmp/ckb_cli/node dir
        2. miner 20 block
        Returns:

        """
        # 1. start 1 ckb node in tmp/ckb_cli/node dir
        cls.node = cls.CkbNode.init_dev_by_port(
            cls.CkbNodeConfigPath.CURRENT_TEST, "ckb_cli/node", 8314, 8315
        )
        cls.node.prepare()
        cls.node.start()
        # 2. miner 20 block
        cls.Miner.make_tip_height_number(cls.node, 20)

    @classmethod
    def teardown_class(cls):
        """
        1. stop ckb node
        2. clean ckb node  tmp dir
        Returns:

        """
        print("stop node and clean")
        cls.node.stop()
        cls.node.clean()

    def test_01_get_indexer_tip(self):
        """
        1.get ckb indexer tip block header
        2.get ckb block header
        3.sync compare ckb block header == ckb indexer tip header
        Returns:

        """
        self.Ckb_cli.version()
        indexer_tip = self.Ckb_cli.get_indexer_tip(api_url=self.node.getClient().url)
        block_number = self.node.getClient().get_tip_block_number()
        assert indexer_tip == block_number

    def test_02_get_cells_by_lock(self):
        """
        1. get block by number return block struct
        2. through block get lock script info
        3. through get cells compare lock args
        Returns:

        """
        block_number = self.node.getClient().get_tip_block_number()
        # 1. get block by number return block struct
        block = self.node.getClient().get_block_by_number(hex(block_number))
        lock = block["transactions"][0]["outputs"][0]["lock"]
        lock_code_hash = lock["code_hash"]
        lock_args = lock["args"]
        # 2. through block get lock script info
        search_json = {
            "script": {
                "code_hash": lock_code_hash,
                "hash_type": "type",
                "args": lock_args,
            },
            "script_type": "lock",
        }

        with open("/tmp/lock.json", "w") as json_file:
            json.dump(search_json, json_file, indent=2)

        limit_number = 3
        #3. through get cells compare lock args
        result = self.Ckb_cli.get_cells(
            limit=3,
            order="asc",
            json_path="/tmp/lock.json",
            api_url=self.node.getClient().url,
        )
        objects_number = len(result["objects"])
        assert objects_number == limit_number

        output_lock = result["objects"][0]["output"]["lock"]
        assert output_lock["code_hash"].split(" ")[0] == lock_code_hash
        assert output_lock["args"] == lock_args
        assert (
            result["objects"][0]["block_number"] <= result["objects"][1]["block_number"]
        )

    def test_03_get_cells_by_type(self):
        """
        1. deploy contract return deploy tx hash
        2. miner until deploy contrct tx hash
        3. get output and compare type_code_hash and type_code_hash
        Returns:

        """
        # 1. deploy contract return deploy tx hash
        deploy_hash = self.Contract.deploy_ckb_contract(
            self.Config.ACCOUNT_PRIVATE_2,
            self.Config.ALWAYS_SUCCESS_CONTRACT_PATH,
            enable_type_id=True,
            api_url=self.node.getClient().url,
        )
        # 2. miner until deploy contrct tx hash
        tx_response = self.Miner.miner_until_tx_committed(self.node, deploy_hash)

        output = tx_response["transaction"]["outputs"][0]
        # 3. get output and compare type_code_hash and type_code_hash
        if output["type"] is not None:
            type_code_hash = output["type"]["code_hash"]
            type_args = output["type"]["args"]
            search_json = {
                "script": {
                    "code_hash": type_code_hash,
                    "hash_type": "type",
                    "args": type_args,
                },
                "script_type": "type",
            }

            with open("/tmp/type.json", "w") as json_file:
                json.dump(search_json, json_file, indent=2)
            result = self.Ckb_cli.get_cells(
                limit=10, json_path="/tmp/type.json", api_url=self.node.getClient().url
            )
            objects_number = len(result["objects"])
            assert objects_number == 1

            output_type = result["objects"][0]["output"]["type"]
            assert output_type["code_hash"] == type_code_hash
            assert output_type["args"] == type_args

        else:
            assert False, "Failed: Output does not contain a 'type' field."

    def test_04_get_cells_filter_by_type_or_lock(self):
        """
        1. deploy contract and return tx hash and miner tx hash which tx status committed
        2. get output struct and type lock args..
        3. get cells and compare search_json_by_lock and by type
        Returns:

        """
        # 1. deploy contract and return tx hash and miner tx hash which tx status committed
        deploy_hash = self.Contract.deploy_ckb_contract(
            self.Config.ACCOUNT_PRIVATE_2,
            self.Config.ALWAYS_SUCCESS_CONTRACT_PATH,
            enable_type_id=True,
            api_url=self.node.getClient().url,
        )
        tx_response = self.Miner.miner_until_tx_committed(self.node, deploy_hash)
        # 2. get output struct and type lock args..
        output = tx_response["transaction"]["outputs"][0]
        lock_code_hash = output["lock"]["code_hash"]
        lock_args = output["lock"]["args"]
        type_code_hash = output["type"]["code_hash"]
        type_args = output["type"]["args"]

        search_json_by_type = {
            "script": {
                "code_hash": lock_code_hash,
                "hash_type": "type",
                "args": lock_args,
            },
            "script_type": "lock",
            "filter": {
                "script": {
                    "code_hash": type_code_hash,
                    "hash_type": "type",
                    "args": type_args,
                }
            },
        }

        with open("/tmp/filter_by_type.json", "w") as json_file:
            json.dump(search_json_by_type, json_file, indent=2)
        by_type_result = self.Ckb_cli.get_cells(
            limit=10,
            json_path="/tmp/filter_by_type.json",
            api_url=self.node.getClient().url,
        )
        objects_number = len(by_type_result["objects"])
        assert objects_number == 1

        search_json_by_lock = {
            "script": {
                "code_hash": type_code_hash,
                "hash_type": "type",
                "args": type_args,
            },
            "script_type": "type",
            "filter": {
                "script": {
                    "code_hash": lock_code_hash,
                    "hash_type": "type",
                    "args": lock_args,
                }
            },
        }
        #3. get cells and compare search_json_by_lock and by type
        with open("/tmp/filter_by_type.json", "w") as json_file:
            json.dump(search_json_by_lock, json_file, indent=2)
        by_lock_result = self.Ckb_cli.get_cells(
            limit=10,
            json_path="/tmp/filter_by_type.json",
            api_url=self.node.getClient().url,
        )

        del by_type_result["last_cursor"]
        del by_lock_result["last_cursor"]
        assert by_type_result == by_lock_result

    def test_05_get_cells_filter_by_output_data(self):
        """
        1. deploy contract and return tx hash and miner this hash status = committed
        2. get transaction return transaction outputs_data and lock code hash and args
        3. get cells search mode use exact return live cell and compare cell number assert
        4. get cells search mode use prefix return live cell and compare cell number assert
        5. get cells search mode use partial return live cell and compare cell number assert
        Returns:

        """
        # 1. deploy contract and return tx hash and miner this hash status = committed
        deploy_hash = self.Contract.deploy_ckb_contract(
            self.Config.ACCOUNT_PRIVATE_2,
            self.Config.SPAWN_CONTRACT_PATH,
            enable_type_id=True,
            api_url=self.node.getClient().url,
        )
        tx_response = self.Miner.miner_until_tx_committed(self.node, deploy_hash)
        # 2. get transaction return transaction outputs_data and lock code hash and args
        outputs_data = tx_response["transaction"]["outputs_data"]
        output_data = outputs_data[0]
        output = tx_response["transaction"]["outputs"][0]
        lock_code_hash = output["lock"]["code_hash"]
        lock_args = output["lock"]["args"]
        # 3. get cells search mode use exact return live cell and compare cell number assert
        # mode: exact
        exact_search_json = {
            "script": {
                "code_hash": lock_code_hash,
                "hash_type": "type",
                "args": lock_args,
            },
            "script_type": "lock",
            "filter": {"output_data": output_data, "output_data_filter_mode": "exact"},
        }

        with open("/tmp/exact.json", "w") as json_file:
            json.dump(exact_search_json, json_file, indent=2)
        exact_result = self.Ckb_cli.get_cells(
            limit=10, json_path="/tmp/exact.json", api_url=self.node.getClient().url
        )
        objects_number = len(exact_result["objects"])
        assert objects_number == 1
        #4. get cells search mode use prefix return live cell and compare cell number assert
        # mode: prefix
        prefix_search_json = {
            "script": {
                "code_hash": lock_code_hash,
                "hash_type": "type",
                "args": lock_args,
            },
            "script_type": "lock",
            "filter": {
                "output_data": output_data[:50],
                "output_data_filter_mode": "prefix",
            },
        }

        with open("/tmp/prefix.json", "w") as json_file:
            json.dump(prefix_search_json, json_file, indent=2)
        exact_result = self.Ckb_cli.get_cells(
            limit=10, json_path="/tmp/prefix.json", api_url=self.node.getClient().url
        )
        objects_number = len(exact_result["objects"])
        assert objects_number == 3
        # 5. get cells search mode use partial return live cell and compare cell number assert
        # mode: partial
        partial_search_json = {
            "script": {
                "code_hash": lock_code_hash,
                "hash_type": "type",
                "args": lock_args,
            },
            "script_type": "lock",
            "filter": {
                "output_data": "0x" + output_data[50:56],
                "output_data_filter_mode": "partial",
            },
        }

        with open("/tmp/partial.json", "w") as json_file:
            json.dump(partial_search_json, json_file, indent=2)
        exact_result = self.Ckb_cli.get_cells(
            limit=10, json_path="/tmp/partial.json", api_url=self.node.getClient().url
        )
        objects_number = len(exact_result["objects"])
        assert objects_number == 1

    def test_06_get_transactions_by_lock(self):
        """
        1. get tip blocknumber and get block struct by number
        2. get output lock script info by block["transactions"][0]["outputs"][0]["lock"]
        3. get transactions and assert block_number and others in indexerTxWithCell Type
        Returns:

        """
        #1. get tip blocknumber and get block struct by number
        block_number = self.node.getClient().get_tip_block_number()
        block = self.node.getClient().get_block_by_number(hex(block_number))
        #2. get output lock script info by block["transactions"][0]["outputs"][0]["lock"]
        lock = block["transactions"][0]["outputs"][0]["lock"]
        lock_code_hash = lock["code_hash"]
        lock_args = lock["args"]
        search_json = {
            "script": {
                "code_hash": lock_code_hash,
                "hash_type": "type",
                "args": lock_args,
            },
            "script_type": "lock",
        }
        #3. get transactions and assert block_number and others in indexerTxWithCell Type
        with open("/tmp/transactions.json", "w") as json_file:
            json.dump(search_json, json_file, indent=2)
        result = self.Ckb_cli.get_transactions(
            limit=10,
            json_path="/tmp/transactions.json",
            api_url=self.node.getClient().url,
        )

        objects_number = len(result["objects"])
        assert objects_number >= 1
        assert "block_number" in result["objects"][0]
        assert "io_index" in result["objects"][0]
        assert "io_type" in result["objects"][0]
        assert "tx_hash" in result["objects"][0]
        assert "tx_index" in result["objects"][0]

    def test_07_get_cells_capacity_by_lock(self):
        """
        1. get tip blocknumber and get block struct by number
        2. get cells capacity and assert block_number and others in Type IndexerCellsCapacity
        Returns:

        """
        #1. get tip blocknumber and get block struct by number
        block_number = self.node.getClient().get_tip_block_number()
        block = self.node.getClient().get_block_by_number(hex(block_number))
        lock = block["transactions"][0]["outputs"][0]["lock"]
        lock_code_hash = lock["code_hash"]
        lock_args = lock["args"]
        search_json = {
            "script": {
                "code_hash": lock_code_hash,
                "hash_type": "type",
                "args": lock_args,
            },
            "script_type": "lock",
        }
        #2. get cells capacity and assert block_number and others in Type IndexerCellsCapacity
        with open("/tmp/cells_capacity.json", "w") as json_file:
            json.dump(search_json, json_file, indent=2)
        result = self.Ckb_cli.get_cells_capacity(
            json_path="/tmp/cells_capacity.json", api_url=self.node.getClient().url
        )

        objects_number = len(result)
        assert objects_number >= 1
        assert "block_hash" in result
        assert "block_number" in result
        assert "capacity" in result
