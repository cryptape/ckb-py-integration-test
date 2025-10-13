from framework.helper.contract import (
    deploy_ckb_contract,
    invoke_ckb_contract,
    get_ckb_contract_codehash,
)
from framework.util import get_project_root
from framework.config import MINER_PRIVATE_1
from framework.helper.miner import miner_until_tx_committed
from test_cases.rpc.node_fixture import get_cluster_indexer


class TestGetTransactions:

    def test_get_transactions(self, get_cluster_indexer):
        cluster = get_cluster_indexer
        deploy_hash = deploy_ckb_contract(
            MINER_PRIVATE_1,
            f"{get_project_root()}/source/contract/always_success",
            enable_type_id=True,
            api_url=cluster.ckb_nodes[0].getClient().url,
        )
        miner_until_tx_committed(cluster.ckb_nodes[0], deploy_hash)
        first_invoke_hash = invoke_ckb_contract(
            account_private=MINER_PRIVATE_1,
            contract_out_point_tx_hash=deploy_hash,
            contract_out_point_tx_index=0,
            type_script_arg="0x02",
            data=f"0x{1:02x}{1:02x}",
            hash_type="type",
            api_url=cluster.ckb_nodes[0].getClient().url,
        )
        miner_until_tx_committed(cluster.ckb_nodes[0], first_invoke_hash)
        for i in range(2, 10):
            invoke_hash = invoke_ckb_contract(
                account_private=MINER_PRIVATE_1,
                contract_out_point_tx_hash=deploy_hash,
                contract_out_point_tx_index=0,
                type_script_arg="0x02",
                data=f"0x{i:02x}{i:02x}",
                hash_type="type",
                api_url=cluster.ckb_nodes[0].getClient().url,
            )
            miner_until_tx_committed(cluster.ckb_nodes[0], invoke_hash)
        invoke_hash = invoke_ckb_contract(
            account_private=MINER_PRIVATE_1,
            contract_out_point_tx_hash=deploy_hash,
            contract_out_point_tx_index=0,
            type_script_arg="0x02",
            data="0xffff00000000ffff",
            hash_type="type",
            api_url=cluster.ckb_nodes[0].getClient().url,
        )
        miner_until_tx_committed(cluster.ckb_nodes[0], invoke_hash)
        codehash = get_ckb_contract_codehash(
            deploy_hash,
            0,
            enable_type_id=True,
            api_url=cluster.ckb_nodes[0].getClient().url,
        )
        # prefix search mode
        search_mode_prefix_results = get_transaction_with_script_search_mode(
            cluster, codehash, "0x02", "prefix"
        )
        tx = cluster.ckb_nodes[0].getClient().get_transaction(first_invoke_hash)
        print("first_invoke_hash:", tx)
        assert search_mode_prefix_results == [
            tx["tx_status"]["block_number"],
            tx["tx_status"]["block_number"],
        ]

        # exact search mode
        search_mode_exact_results = get_transaction_with_script_search_mode(
            cluster, codehash, "0x02", "exact"
        )
        assert search_mode_exact_results == [
            tx["tx_status"]["block_number"],
            tx["tx_status"]["block_number"],
        ]

        # partial search mode
        # partial search mode & indexer:Error: Indexer: Invalid params the CKB indexer doesn't support search_key.script_search_mode partial search mode, please use the CKB rich-indexer for such search
        search_mode_partial_results = (
            get_transaction_with_script_search_mode_byRichIndexer(
                cluster, codehash, "0x02", "partial"
            )
        )
        assert search_mode_partial_results == [tx["tx_status"]["block_number"]]

        # partial/exact/prefix not support by indexer
        cell_data_filter_types = ["prefix", "exact", "partial"]
        for cell_data_filter_type in cell_data_filter_types:
            try:
                get_transactions_with_output_data_byIndexer(
                    cluster, codehash, "0x02", "exact", "0x02", cell_data_filter_type
                )
            except Exception as e:
                print(f"Caught an exception: {e}")
                assert (
                    "Invalid params doesn't support search_key.filter.output_data parameter"
                    in str(e)
                ), f"Unexpected exception: {e}"


def get_transaction_with_script_search_mode_byRichIndexer(
    cluster, codehash, args, script_search_mode
):
    results = []
    ret = (
        cluster.ckb_nodes[1]
        .getClient()
        .get_transactions(
            {
                "script": {"code_hash": codehash, "hash_type": "type", "args": args},
                "script_type": "type",
                "script_search_mode": script_search_mode,
            },
            "asc",
            "0xff",
            None,
        )
    )

    results.append(ret["objects"][0]["block_number"])
    return results


def get_transaction_with_script_search_mode(
    cluster, codehash, args, script_search_mode
):
    results = []

    for node in cluster.ckb_nodes:
        ret = node.getClient().get_transactions(
            {
                "script": {"code_hash": codehash, "hash_type": "type", "args": args},
                "script_type": "type",
                "script_search_mode": script_search_mode,
            },
            "asc",
            "0xff",
            None,
        )

        results.append(ret["objects"][0]["block_number"])

    return results


def get_transactions_with_output_data_byIndexer(
    cluster, codehash, args, script_search_mode, output_data, output_data_filter_mode
):
    results = []
    ret = (
        cluster.ckb_nodes[0]
        .getClient()
        .get_transactions(
            {
                "script": {"code_hash": codehash, "hash_type": "type", "args": args},
                "script_type": "type",
                "script_search_mode": script_search_mode,
                "filter": {
                    "output_data": output_data,
                    "output_data_filter_mode": output_data_filter_mode,
                },
            },
            "asc",
            "0xff",
            None,
        )
    )

    results.append(ret["objects"][0]["block_number"])
    return results


def get_transactions_with_output_data_byRichIndexer(
    cluster, codehash, args, script_search_mode, output_data, output_data_filter_mode
):
    results = []
    ret = (
        cluster.ckb_nodes[1]
        .getClient()
        .get_transactions(
            {
                "script": {"code_hash": codehash, "hash_type": "type", "args": args},
                "script_type": "type",
                "script_search_mode": script_search_mode,
                "filter": {
                    "output_data": output_data,
                    "output_data_filter_mode": output_data_filter_mode,
                },
            },
            "asc",
            "0xff",
            None,
        )
    )

    results.append(ret["objects"][0]["block_number"])
    return results
