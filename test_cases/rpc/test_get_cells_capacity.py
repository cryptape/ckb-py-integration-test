from framework.helper.contract import deploy_ckb_contract, invoke_ckb_contract, get_ckb_contract_codehash
from framework.util import get_project_root
from framework.config import MINER_PRIVATE_1
from framework.helper.miner import miner_until_tx_committed
from test_cases.rpc.node_fixture import get_cluster


class TestGetCellsCapacity:

    def test_get_cells_capacity_output_data_filter_mode(self, get_cluster):
        cluster = get_cluster
        deploy_hash = deploy_ckb_contract(MINER_PRIVATE_1,
                                          f"{get_project_root()}/source/contract/always_success",
                                          enable_type_id=True,
                                          api_url=cluster.ckb_nodes[0].getClient().url)
        miner_until_tx_committed(cluster.ckb_nodes[0], deploy_hash)
        for i in range(1, 10):
            invoke_hash = invoke_ckb_contract(account_private=MINER_PRIVATE_1,
                                              contract_out_point_tx_hash=deploy_hash,
                                              contract_out_point_tx_index=0,
                                              type_script_arg="0x02", data=f"0x{i:02x}{i:02x}",
                                              hash_type="type",
                                              api_url=cluster.ckb_nodes[0].getClient().url)
            miner_until_tx_committed(cluster.ckb_nodes[0], invoke_hash)
        invoke_hash = invoke_ckb_contract(account_private=MINER_PRIVATE_1,
                                          contract_out_point_tx_hash=deploy_hash,
                                          contract_out_point_tx_index=0,
                                          type_script_arg="0x02", data="0xffff00000000ffff",
                                          hash_type="type",
                                          api_url=cluster.ckb_nodes[0].getClient().url)
        miner_until_tx_committed(cluster.ckb_nodes[0], invoke_hash)

        codehash = get_ckb_contract_codehash(deploy_hash, 0,
                                             enable_type_id=True,
                                             api_url=cluster.ckb_nodes[0].getClient().url)
        # output_data_filter_mode : prefix

        ret = cluster.ckb_nodes[0].getClient().get_cells({
            "script": {
                "code_hash": codehash,
                "hash_type": "type",
                "args": "0x02"
            },
            "script_type": "type",
            "filter": {
                "output_data": "0x01",
                "output_data_filter_mode": "prefix"
            }
        }, "asc", "0xff", None)

        get_cells_capacity_ret = cluster.ckb_nodes[0].getClient().get_cells_capacity({
            "script": {
                "code_hash": codehash,
                "hash_type": "type",
                "args": "0x02"
            },
            "script_type": "type",
            "filter": {
                "output_data": "0x01",
                "output_data_filter_mode": "prefix"
            }
        })

        assert ret['objects'][0]['output_data'] == '0x0101'
        assert get_cells_capacity_ret['capacity'] == ret['objects'][0]['output']['capacity']

        ret = cluster.ckb_nodes[0].getClient().get_cells({
            "script": {
                "code_hash": codehash,
                "hash_type": "type",
                "args": "0x02"
            },
            "script_type": "type",
            "filter": {
                "output_data": "0x02",
                "output_data_filter_mode": "prefix"
            }
        }, "asc", "0xff", None)
        get_cells_capacity_ret = cluster.ckb_nodes[0].getClient().get_cells_capacity({
            "script": {
                "code_hash": codehash,
                "hash_type": "type",
                "args": "0x02"
            },
            "script_type": "type",
            "filter": {
                "output_data": "0x02",
                "output_data_filter_mode": "prefix"
            }
        })
        assert ret['objects'][0]['output_data'] == '0x0202'
        assert get_cells_capacity_ret['capacity'] == ret['objects'][0]['output']['capacity']

        # output_data_filter_mode : exact
        ret = cluster.ckb_nodes[0].getClient().get_cells({
            "script": {
                "code_hash": codehash,
                "hash_type": "type",
                "args": "0x02"
            },
            "script_type": "type",
            "filter": {
                "output_data": "0x0303",
                "output_data_filter_mode": "exact"
            }
        }, "asc", "0xff", None)
        get_cells_capacity_ret = cluster.ckb_nodes[0].getClient().get_cells_capacity({
            "script": {
                "code_hash": codehash,
                "hash_type": "type",
                "args": "0x02"
            },
            "script_type": "type",
            "filter": {
                "output_data": "0x0303",
                "output_data_filter_mode": "exact"
            }
        })
        assert ret['objects'][0]['output_data'] == '0x0303'
        assert get_cells_capacity_ret['capacity'] == ret['objects'][0]['output']['capacity']

        # output_data_filter_mode : partial
        ret = cluster.ckb_nodes[0].getClient().get_cells({
            "script": {
                "code_hash": codehash,
                "hash_type": "type",
                "args": "0x02"
            },
            "script_type": "type",
            "filter": {
                "output_data": "0x00000000ffff",
                "output_data_filter_mode": "partial"
            }
        }, "asc", "0xff", None)
        get_cells_capacity_ret = cluster.ckb_nodes[0].getClient().get_cells_capacity({
            "script": {
                "code_hash": codehash,
                "hash_type": "type",
                "args": "0x02"
            },
            "script_type": "type",
            "filter": {
                "output_data": "0x00000000ffff",
                "output_data_filter_mode": "partial"
            }
        })
        assert ret['objects'][0]['output_data'] == '0xffff00000000ffff'
        assert get_cells_capacity_ret['capacity'] == ret['objects'][0]['output']['capacity']
