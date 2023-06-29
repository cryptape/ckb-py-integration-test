from framework.helper.ckb_cli import *
from framework.test_node import CkbNode
from framework.rpc import RPCClient
import hashlib
import time

from abc import ABC, abstractmethod


class CKbContract(ABC):

    @abstractmethod
    def deploy(self, account_private, node: CkbNode):
        pass

    @abstractmethod
    def get_deploy_hash_and_index(self) -> (str, int):
        pass

    @abstractmethod
    def get_arg_and_data(self, key) -> (str, str):
        pass


def deploy_ckb_contract(private_key, contract_path, fee_rate=2000, enable_type_id=True,
                        api_url="http://127.0.0.1:8114"):
    """

    Args:
        private_key:
        contract_path:
        api_url:

    Returns: tx_hash
    :param api_url:
    :param enable_type_id:

    """
    if enable_type_id:
        tmp_tx_info_path = f"/tmp/tx-{time.time_ns().real}.json"
        tmp_deploy_toml_path = "/tmp/deploy1.toml"
        deploy_toml_str = get_deploy_toml_config(private_key, contract_path, enable_type_id)
        with open(tmp_deploy_toml_path, "w") as f:
            f.write(deploy_toml_str)
        account = util_key_info_by_private_key(private_key)
        deploy_gen_txs(account["address"]["testnet"], tmp_deploy_toml_path, tmp_tx_info_path, api_url)
        deploy_sign_txs(private_key, tmp_tx_info_path, api_url)
        deploy_tx_result = deploy_apply_txs(tmp_tx_info_path, api_url)
        return deploy_tx_result["cell_tx"]

    # rand ckb address ,provider contract cell cant be used
    to_ckb_address = "ckt1qzda0cr08m85hc8jlnfp3zer7xulejywt49kt2rr0vthywaa50xwsqwgx292hnvmn68xf779vmzrshpmm6epn4g6eqkaw"
    with open(contract_path, "rb") as f:
        # +100 provider capacity enough deploy contract
        capacity = len(f.read()) + 100
    cmd = f"export API_URL={api_url} &&  echo {private_key} > /tmp/tmp.data && {cli_path} wallet transfer " \
          f"--privkey-path /tmp/tmp.data --to-address  {to_ckb_address}  --capacity {capacity} --to-data-path {contract_path}  --fee-rate {fee_rate}" \
          f" && rm /tmp/tmp.data"
    return run_command(cmd).replace('\n', '')


def get_ckb_contract_codehash(tx_hash, tx_index, enable_type_id=True, api_url="http://127.0.0.1:8114"):
    if enable_type_id:
        type_arg = RPCClient(api_url).get_transaction(tx_hash)["transaction"]["outputs"][tx_index]['type'][
            'args'].replace("0x", "")
        # code_hash = "0x00000000000000000000000000000000000000000000000000545950455f4944"
        # hash_type = "type" #01
        # ckb.script.pack
        data = bytes.fromhex(
            f"5500000010000000300000003100000000000000000000000000000000000000000000000000000000545950455f49440120000000{type_arg}")
    else:
        tx_data = RPCClient(api_url).get_transaction(tx_hash)["transaction"]["outputs_data"][tx_index]
        data = bytes.fromhex(tx_data.replace("0x", ""))
    personalization = "ckb-default-hash".encode("utf-8")
    # cal blake 2b hash
    hash_object = hashlib.blake2b(digest_size=32, person=personalization)
    hash_object.update(data)
    hex_digest = hash_object.hexdigest()
    return f"0x{hex_digest}"


def invoke_ckb_contract(account_private, contract_out_point_tx_hash, contract_out_point_tx_index, type_script_arg,
                        hash_type="type",
                        data="0x", fee=1000,
                        api_url="http://127.0.0.1:8114"):
    """

    Args:
        account_private:
        contract_out_point_tx_hash:
        contract_out_point_tx_index:
        type_script_arg:
        hash_type:  data ,data1,type data2
        data:
        fee:
        api_url:

    Returns:

    """
    if hash_type == "type":
        contract_code_hash = get_ckb_contract_codehash(contract_out_point_tx_hash, contract_out_point_tx_index,
                                                       enable_type_id=True,
                                                       api_url=api_url)
    else:
        contract_code_hash = get_ckb_contract_codehash(contract_out_point_tx_hash, contract_out_point_tx_index,
                                                       enable_type_id=False,
                                                       api_url=api_url)
    # get input_cell
    account = util_key_info_by_private_key(account_private)
    account_address = account["address"]["testnet"]
    account_live_cells = wallet_get_live_cells(account_address, api_url=api_url)
    assert len(account_live_cells['live_cells']) > 0
    input_cell_out_point = {
        'tx_hash': account_live_cells['live_cells'][0]['tx_hash'],
        'index': account_live_cells['live_cells'][0]['output_index']
    }
    # get output_cells.cap = input_cell.cap - fee
    #  "capacity": "21685.0 (CKB)",
    output_cell_capacity = float(
        account_live_cells['live_cells'][0]['capacity'].replace('(CKB)', "").strip()) * 100000000 - fee

    output_cell = {
        "capacity": hex(int(output_cell_capacity)),
        # rand ckb address for pass ckb-cli check lock address
        "lock": {
            "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
            "hash_type": "type",
            "args": "0x470dcdc5e44064909650113a274b3b36aecb6dc7"
        },
        "type": {
            "code_hash": contract_code_hash,
            "hash_type": hash_type,
            "args": type_script_arg
        }
    }
    # add dep
    cell_dep = {
        'tx_hash': contract_out_point_tx_hash,
        'index': hex(contract_out_point_tx_index)
    }
    # tx file init
    tmp_tx_file = "/tmp/demo.json"
    tx_init(tmp_tx_file, api_url)
    tx_add_multisig_config(account_address, tmp_tx_file, api_url)
    # add input
    tx_add_input(input_cell_out_point['tx_hash'], input_cell_out_point['index'], tmp_tx_file, api_url)

    # add output
    tx_add_type_out_put(output_cell["type"]["code_hash"], output_cell["type"]["hash_type"], output_cell["type"]["args"],
                        output_cell["capacity"], data, tmp_tx_file)
    # add dep
    tx_add_cell_dep(cell_dep['tx_hash'], cell_dep['index'], tmp_tx_file)
    # sign
    sign_data = tx_sign_inputs(account_private, tmp_tx_file, api_url)
    tx_add_signature(sign_data[0]['lock-arg'], sign_data[0]['signature'], tmp_tx_file, api_url)
    tx_info(tmp_tx_file, api_url)
    # send tx return hash
    return tx_send(tmp_tx_file, api_url).strip()
