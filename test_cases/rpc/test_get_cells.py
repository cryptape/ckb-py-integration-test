from framework.helper.contract import deploy_ckb_contract, invoke_ckb_contract, get_ckb_contract_codehash
from framework.util import get_project_root
from framework.config import MINER_PRIVATE_1
from framework.helper.miner import miner_until_tx_committed
from test_cases.rpc.node_fixture import get_cluster_indexer


class TestGetCells:

    def test_get_cells_output_data_filter_mode(self, get_cluster_indexer):
        cluster = get_cluster_indexer
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

        args = "0x02"
        # output_data_filter_mode: prefix
        output_data_prefix_results = get_cells_with_output_data(cluster, codehash, args, "0x01", "prefix")
        assert output_data_prefix_results == ['0x0101', '0x0101']

        output_data_prefix_results = get_cells_with_output_data(cluster, codehash, args, "0x02", "prefix")
        assert output_data_prefix_results == ['0x0202', '0x0202']

        # output_data_filter_mode: exact
        output_data_exact_results = get_cells_with_output_data(cluster, codehash, args, "0x0303", "exact")
        assert output_data_exact_results == ['0x0303', '0x0303']

        # output_data_filter_mode: partial
        output_data_partial_results = get_cells_with_output_data(cluster, codehash, args, "0x00000000ffff", "partial")
        assert output_data_partial_results == ['0xffff00000000ffff',
                                               '0xffff00000000ffff']

        # script_search_mode: prefix
        search_mode_prefix_results = get_cells_with_script_search_mode(cluster, codehash, args, "prefix", "0x01",
                                                                       "prefix")
        assert search_mode_prefix_results == ['0x0101', '0x0101']

        # script_search_mode: exact
        search_mode_exact_results = get_cells_with_script_search_mode(cluster, codehash, args, "exact", "0x02",
                                                                      "prefix")
        assert search_mode_exact_results == ['0x0202', '0x0202']

        # script_search_mode: partial
        try:
            get_cells_with_output_data_byIndexer(cluster, codehash, args, "partial", "0x02", "prefix")
        except Exception as e:
            print(f"Caught an exception: {e}")
            assert "Invalid params the CKB indexer doesn't support search_key.script_search_mode partial search mode" in str(
                e), f"Unexpected exception: {e}"


def get_cells_with_output_data(cluster, codehash, args, output_data, output_data_filter_mode):
    results = []

    for node in cluster.ckb_nodes:
        ret = node.getClient().get_cells({
            "script": {
                "code_hash": codehash,
                "hash_type": "type",
                "args": args
            },
            "script_type": "type",
            "filter": {
                "output_data": output_data,
                "output_data_filter_mode": output_data_filter_mode
            }
        }, "asc", "0xff", None)

        results.append(ret['objects'][0]['output_data'])

    return results


def get_cells_with_script_search_mode(cluster, codehash, args, script_search_mode, output_data,
                                      output_data_filter_mode):
    results = []

    for node in cluster.ckb_nodes:
        ret = node.getClient().get_cells({
            "script": {
                "code_hash": codehash,
                "hash_type": "type",
                "args": args
            },
            "script_type": "type",
            "script_search_mode": script_search_mode,
            "filter": {
                "output_data": output_data,
                "output_data_filter_mode": output_data_filter_mode
            }
        }, "asc", "0xff", None)

        results.append(ret['objects'][0]['output_data'])

    return results


def get_cells_with_output_data_byIndexer(cluster, codehash, args, script_search_mode,
                                         output_data, output_data_filter_mode):
    results = []
    ret = cluster.ckb_nodes[0].getClient().get_cells({
        "script": {
            "code_hash": codehash,
            "hash_type": "type",
            "args": args
        },
        "script_type": "type",
        "script_search_mode": script_search_mode,
        "filter": {
            "output_data": output_data,
            "output_data_filter_mode": output_data_filter_mode
        }
    }, "asc", "0xff", None)

    results.append(ret['objects'][0]["block_number"])
    return results
