import json
import time

from framework.basic import CkbTest


class TestCkbCliRpc114(CkbTest):

    @classmethod
    def setup_class(cls):
        cls.node = cls.CkbNode.init_dev_by_port(cls.CkbNodeConfigPath.CURRENT_TEST, "ckb_cli/node", 8314, 8315)
        cls.node.prepare()
        cls.node.start()
        cls.Miner.make_tip_height_number(cls.node, 20)

    @classmethod
    def teardown_class(cls):
        print("stop node and clean")
        cls.node.stop()
        cls.node.clean()

    def test_01_get_indexer_tip(self):
        self.Ckb_cli.version()
        indexer_tip = self.Ckb_cli.get_indexer_tip(api_url=self.node.getClient().url)
        block_number = self.node.getClient().get_tip_block_number()
        assert indexer_tip == block_number

    def test_02_get_cells_by_lock(self):
        block_number = self.node.getClient().get_tip_block_number()
        block = self.node.getClient().get_block_by_number(hex(block_number))
        lock = block['transactions'][0]['outputs'][0]['lock']
        lock_code_hash = lock['code_hash']
        lock_args = lock['args']
        search_json = {
            "script": {
                "code_hash": lock_code_hash,
                "hash_type": "type",
                "args": lock_args
            },
            "script_type": "lock"
        }

        with open('/tmp/lock.json', 'w') as json_file:
            json.dump(search_json, json_file, indent=2)

        limit_number = 3
        result = self.Ckb_cli.get_cells(limit=3, order="asc", json_path='/tmp/lock.json',
                                        api_url=self.node.getClient().url)
        objects_number = len(result['objects'])
        assert objects_number == limit_number

        output_lock = result['objects'][0]['output']['lock']
        assert output_lock['code_hash'].split(" ")[0] == lock_code_hash
        assert output_lock['args'] == lock_args
        assert result['objects'][0]['block_number'] <= result['objects'][1]['block_number']

    def test_03_get_cells_by_type(self):
        deploy_hash = self.Contract.deploy_ckb_contract(self.Config.ACCOUNT_PRIVATE_2,
                                                        self.Config.ALWAYS_SUCCESS_CONTRACT_PATH,
                                                        enable_type_id=True,
                                                        api_url=self.node.getClient().url)
        tx_response = self.Miner.miner_until_tx_committed(self.node, deploy_hash)

        output = tx_response['transaction']['outputs'][0]
        if output['type'] is not None:
            type_code_hash = output['type']['code_hash']
            type_args = output['type']['args']
            search_json = {
                "script": {
                    "code_hash": type_code_hash,
                    "hash_type": 'type',
                    "args": type_args
                },
                "script_type": "type"
            }

            with open('/tmp/type.json', 'w') as json_file:
                json.dump(search_json, json_file, indent=2)
            result = self.Ckb_cli.get_cells(limit=10, json_path='/tmp/type.json', api_url=self.node.getClient().url)
            objects_number = len(result['objects'])
            assert objects_number == 1

            output_type = result['objects'][0]['output']['type']
            assert output_type['code_hash'] == type_code_hash
            assert output_type['args'] == type_args

        else:
            assert False, "Failed: Output does not contain a 'type' field."

    def test_04_get_cells_filter_by_type_or_lock(self):
        deploy_hash = self.Contract.deploy_ckb_contract(self.Config.ACCOUNT_PRIVATE_2,
                                                        self.Config.ALWAYS_SUCCESS_CONTRACT_PATH,
                                                        enable_type_id=True,
                                                        api_url=self.node.getClient().url)
        tx_response = self.Miner.miner_until_tx_committed(self.node, deploy_hash)

        output = tx_response['transaction']['outputs'][0]
        lock_code_hash = output['lock']['code_hash']
        lock_args = output['lock']['args']
        type_code_hash = output['type']['code_hash']
        type_args = output['type']['args']

        search_json_by_type = {
            "script": {
                "code_hash": lock_code_hash,
                "hash_type": "type",
                "args": lock_args
            },
            "script_type": "lock",
            "filter": {
                "script": {
                    "code_hash": type_code_hash,
                    "hash_type": "type",
                    "args": type_args
                }
            }

        }

        with open('/tmp/filter_by_type.json', 'w') as json_file:
            json.dump(search_json_by_type, json_file, indent=2)
        by_type_result = self.Ckb_cli.get_cells(limit=10, json_path='/tmp/filter_by_type.json',
                                                api_url=self.node.getClient().url)
        objects_number = len(by_type_result['objects'])
        assert objects_number == 1

        search_json_by_lock = {
            "script": {
                "code_hash": type_code_hash,
                "hash_type": "type",
                "args": type_args
            },
            "script_type": "type",
            "filter": {
                "script": {
                    "code_hash": lock_code_hash,
                    "hash_type": "type",
                    "args": lock_args
                }
            }

        }

        with open('/tmp/filter_by_type.json', 'w') as json_file:
            json.dump(search_json_by_lock, json_file, indent=2)
        by_lock_result = self.Ckb_cli.get_cells(limit=10, json_path='/tmp/filter_by_type.json',
                                                api_url=self.node.getClient().url)

        del by_type_result['last_cursor']
        del by_lock_result['last_cursor']
        assert by_type_result == by_lock_result

    def test_05_get_cells_filter_by_output_data(self):
        deploy_hash = self.Contract.deploy_ckb_contract(self.Config.ACCOUNT_PRIVATE_2,
                                                        self.Config.SPAWN_CONTRACT_PATH,
                                                        enable_type_id=True,
                                                        api_url=self.node.getClient().url)
        tx_response = self.Miner.miner_until_tx_committed(self.node, deploy_hash)
        outputs_data = tx_response['transaction']['outputs_data']
        output_data = outputs_data[0]
        output = tx_response['transaction']['outputs'][0]
        lock_code_hash = output['lock']['code_hash']
        lock_args = output['lock']['args']

        # mode: exact
        exact_search_json = {
            "script": {
                "code_hash": lock_code_hash,
                "hash_type": "type",
                "args": lock_args
            },
            "script_type": "lock",
            "filter": {
                "output_data": output_data,
                "output_data_filter_mode": "exact"
            }
        }

        with open('/tmp/exact.json', 'w') as json_file:
            json.dump(exact_search_json, json_file, indent=2)
        exact_result = self.Ckb_cli.get_cells(limit=10, json_path='/tmp/exact.json',
                                              api_url=self.node.getClient().url)
        objects_number = len(exact_result['objects'])
        assert objects_number == 1

        # mode: prefix
        prefix_search_json = {
            "script": {
                "code_hash": lock_code_hash,
                "hash_type": "type",
                "args": lock_args
            },
            "script_type": "lock",
            "filter": {
                "output_data": output_data[:50],
                "output_data_filter_mode": "prefix"
            }
        }

        with open('/tmp/prefix.json', 'w') as json_file:
            json.dump(prefix_search_json, json_file, indent=2)
        exact_result = self.Ckb_cli.get_cells(limit=10, json_path='/tmp/prefix.json',
                                              api_url=self.node.getClient().url)
        objects_number = len(exact_result['objects'])
        assert objects_number == 3

        # mode: partial
        partial_search_json = {
            "script": {
                "code_hash": lock_code_hash,
                "hash_type": "type",
                "args": lock_args
            },
            "script_type": "lock",
            "filter": {
                "output_data": "0x" + output_data[50:56],
                "output_data_filter_mode": "partial"
            }
        }

        with open('/tmp/partial.json', 'w') as json_file:
            json.dump(partial_search_json, json_file, indent=2)
        exact_result = self.Ckb_cli.get_cells(limit=10, json_path='/tmp/partial.json',
                                              api_url=self.node.getClient().url)
        objects_number = len(exact_result['objects'])
        assert objects_number == 1

    def test_06_get_transactions_by_lock(self):
        block_number = self.node.getClient().get_tip_block_number()
        block = self.node.getClient().get_block_by_number(hex(block_number))
        lock = block['transactions'][0]['outputs'][0]['lock']
        lock_code_hash = lock['code_hash']
        lock_args = lock['args']
        search_json = {
            "script": {
                "code_hash": lock_code_hash,
                "hash_type": "type",
                "args": lock_args
            },
            "script_type": "lock"
        }

        with open('/tmp/transactions.json', 'w') as json_file:
            json.dump(search_json, json_file, indent=2)
        result = self.Ckb_cli.get_transactions(limit=10, json_path='/tmp/transactions.json',
                                               api_url=self.node.getClient().url)

        objects_number = len(result['objects'])
        assert objects_number >= 1
        assert 'block_number' in result['objects'][0]
        assert 'io_index' in result['objects'][0]
        assert 'io_type' in result['objects'][0]
        assert 'tx_hash' in result['objects'][0]
        assert 'tx_index' in result['objects'][0]

    def test_07_get_cells_capacity_by_lock(self):
        block_number = self.node.getClient().get_tip_block_number()
        block = self.node.getClient().get_block_by_number(hex(block_number))
        lock = block['transactions'][0]['outputs'][0]['lock']
        lock_code_hash = lock['code_hash']
        lock_args = lock['args']
        search_json = {
            "script": {
                "code_hash": lock_code_hash,
                "hash_type": "type",
                "args": lock_args
            },
            "script_type": "lock"
        }

        with open('/tmp/cells_capacity.json', 'w') as json_file:
            json.dump(search_json, json_file, indent=2)
        result = self.Ckb_cli.get_cells_capacity(json_path='/tmp/cells_capacity.json',
                                                 api_url=self.node.getClient().url)

        objects_number = len(result)
        assert objects_number >= 1
        assert 'block_hash' in result
        assert 'block_number' in result
        assert 'capacity' in result
