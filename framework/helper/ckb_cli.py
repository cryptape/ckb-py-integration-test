import json
import re

from framework.test_node import CkbNodeConfigPath
from framework.util import get_project_root
from framework.util import run_command

# cli_path = "cd {root_path}/{cli_path} && ./ckb-cli".format(root_path=get_project_root(),
#                                                            cli_path=CkbNodeConfigPath.CURRENT_TEST.ckb_bin_path)
cli_path = f"cd {get_project_root()}/source && ./ckb-cli"

def wallet_get_capacity(ckb_address, api_url='http://127.0.0.1:8114'):
    """
    MacBook-Pro-4 0.111.0 % ./ckb-cli  wallet get-capacity
    --address ckt1qzda0cr08m85hc8jlnfp3zer7xulejywt49kt2rr0vthywaa50xwsqw6vjzy9kahx3lyvlgap8dp8ewd8g80pcgcexzrj
    total: 0.0 (CKB)

    :param ckb_address:
    :param api_url:
    :return:
    """
    cmd = "export API_URL={api_url} && {ckb_cli} wallet get-capacity " \
          "--address {ckb_address}".format(api_url=api_url,
                                           ckb_cli=cli_path,
                                           ckb_address=ckb_address)
    capacity_response = run_command(cmd)
    pattern = r"\d+(\.\d+)?"
    match = re.search(pattern, capacity_response)

    if match:
        number = float(match.group())
        return number
    else:
        Exception(f"Number not found :{capacity_response}")


def wallet_get_live_cells(ckb_address, api_url='http://127.0.0.1:8114'):
    """
    ./ckb-cli wallet get-live-cells --address
    ckt1qzda0cr08m85hc8jlnfp3zer7xulejywt49kt2rr0vthywaa50xwsqwgx292hnvmn68xf779vmzrshpmm6epn4c0cgwga
    --output-format json
    {
      "live_cells": [
        {
          "capacity": "21685.0 (CKB)",
          "data_bytes": 21624,
          "index": {
            "output_index": 0,
            "tx_index": 1
          },
          "lock_hash": "0x32e555f3ff8e135cece1351a6a2971518392c1e30375c1e006ad0ce8eac07947",
          "mature": true,
          "number": 803,
          "output_index": 0,
          "tx_hash": "0x069f78bd0dd62c2f0a5ca500605a8410b61735044b4fb6d56b7c93c9de18a177",
          "type_hashes": null
        },
        {
          "capacity": "65.0 (CKB)",
          "data_bytes": 4,
          "index": {
            "output_index": 0,
            "tx_index": 2
          },
          "lock_hash": "0x32e555f3ff8e135cece1351a6a2971518392c1e30375c1e006ad0ce8eac07947",
          "mature": true,
          "number": 803,
          "output_index": 0,
          "tx_hash": "0xd8d05eae2c8fad0ed88e7a0b8adb536e0f0f370f742c1a55f03d48f3f12eb9d1",
          "type_hashes": null
        },
        {
          "capacity": "19999978249.99977444 (CKB)",
          "data_bytes": 0,
          "index": {
            "output_index": 1,
            "tx_index": 2
          },
          "lock_hash": "0x32e555f3ff8e135cece1351a6a2971518392c1e30375c1e006ad0ce8eac07947",
          "mature": true,
          "number": 803,
          "output_index": 1,
          "tx_hash": "0xd8d05eae2c8fad0ed88e7a0b8adb536e0f0f370f742c1a55f03d48f3f12eb9d1",
          "type_hashes": null
        }
      ]
    }


    Args:
        ckb_address:
        api_url:

    Returns:

    """
    cmd = f"export API_URL={api_url} && {cli_path} wallet get-live-cells --address {ckb_address} --output-format json"
    return json.loads(run_command(cmd))


def wallet_transfer_by_private_key(private_key, to_ckb_address, capacity, api_url="http://127.0.0.1:8114",
                                   fee_rate="1000"):
    """
    MacBook-Pro-4 0.111.0 % MacBook-Pro-4 0.111.0 % export API_URL=http://127.0.0.1:8115 &&  echo
    0xd00c06bfd800d27397002dca6fb0993d5ba6399b4238b2f29ee9deb97593d2bc > /tmp/tmp.data && ./ckb-cli wallet transfer --
    privkey-path address1.data --to-address
     ckt1qzda0cr08m85hc8jlnfp3zer7xulejywt49kt2rr0vthywaa50xwsq28phxutezqvjgfv5q38gn5kwek4m9km3cmajeqs  --capacity 88
     --fee-rate 1511 --skip-check-to-address && rm /tmp/tmp.data

    0x451eb73e98d835ade44eab8125153af09e3d36807162417cb6a9f584b58bfd2e

    :param private_key:
    :param to_ckb_address:
    :param capacity:
    :return:

    Args:
        api_url: default ckb rpc url
        fee_rate: default tx fee
    """
    cmd = f"export API_URL={api_url} &&  echo {private_key} > /tmp/tmp.data && {cli_path} wallet transfer " \
          f"--privkey-path /tmp/tmp.data --to-address  {to_ckb_address}  --capacity {capacity}  --fee-rate {fee_rate} --skip-check-to-address " \
          f" && rm /tmp/tmp.data"
    return run_command(cmd).replace('\n', '')


def version():
    """
    MacBook-Pro-4 0.111.0 % ./ckb-cli --version
    ckb-cli 1.4.0 (33bd1a1 2023-03-27)

    :return:
    """
    cmd = "{ckb_cli} --version".format(ckb_cli=cli_path)
    return run_command(cmd)


def deploy_gen_txs(from_address, deployment_config_path, tx_info_path, api_url="http://127.0.0.1:8114"):
    """
    ./ckb-cli deploy gen-txs \
    --deployment-config ./deployment.toml \
    --migration-dir ./migrations \
    --from-address ckt1qzda0cr08m85hc8jlnfp3zer7xulejywt49kt2rr0vthywaa50xwsq28phxutezqvjgfv5q38gn5kwek4m9km3cmajeqs \
    --info-file info123.json
    ==== Cell transaction ====
    [cell] NewAdded , name: compact_udt_lock, old-capacity: 0.0, new-capacity: 21685.0
    > old total capacity: 0.0 (CKB) (removed items not included)
    > new total capacity: 21685.0 (CKB)
    [transaction fee]: 0.00022088
    ==== DepGroup transaction ====
    [dep_group] NewAdded , name: my_dep_group, old-capacity: 0.0, new-capacity: 65.0
    > old total capacity: 0.0 (CKB) (removed items not included)
    > new total capacity: 65.0 (CKB)
    [transaction fee]: 0.00000468
    status: success

    Args:
        from_address:
        deployment_config_path:
        tx_info_path:
        api_url:

    Returns:

    """
    cmd = f"export API_URL={api_url} && " \
          f" rm -rf /tmp/migrations && " \
          f"mkdir /tmp/migrations && " \
          f"{cli_path} deploy gen-txs \
    --deployment-config {deployment_config_path} \
    --migration-dir /tmp/migrations \
    --from-address {from_address} \
    --info-file {tx_info_path}"
    return run_command(cmd)


def deploy_sign_txs(account_private, tx_info_path, api_url="http://127.0.0.1:8114"):
    """
    ./ckb-cli deploy sign-txs --privkey-path accout2.private --add-signatures --info-file info12.json
    cell_tx_signatures:
      0x470dcdc5e44064909650113a274b3b36aecb6dc7:
      0x024bb5507c5edce342763b8d6139a73b6c4b53664b578153a2bc23aedb4819195d0d3c959e
      5f9450eb8c6de4492fcb8ea5d6e9eab2f33871273d22f6ecf326b401
    dep_group_tx_signatures:
      0x470dcdc5e44064909650113a274b3b36aecb6dc7:
      0xba09e8b4cc7a366eb1eb97d17accaf3616f4ebd1307877e00e60cd626e299a9b48122589bd
      d143e588bc5d8bd12b28f165f41255d4b05506995c769fc963d31601

    Returns:

    """
    cmd = f"export API_URL={api_url} && " \
          f"echo {account_private} > /tmp/account.private &&" \
          f" {cli_path} deploy sign-txs --privkey-path /tmp/account.private --add-signatures --info-file {tx_info_path}"
    return run_command(cmd)


def deploy_apply_txs(tx_info_path, api_url="http://127.0.0.1:8114"):
    """
    ./ckb-cli deploy apply-txs --migration-dir ./migrations --info-file info12.json
    > [send cell transaction]: 0xed5981d9e21506e7113f6dbf899152c8a92e5a48b1ca419a992e55d034a7695e
    > [send dep group transaction]: 0xbf64009fb91a0b15ca4db42a8c9ae4d3d11aae89fa4fd797eca4614fbfd64d1d
    cell_tx: 0xed5981d9e21506e7113f6dbf899152c8a92e5a48b1ca419a992e55d034a7695e
    dep_group_tx: 0xbf64009fb91a0b15ca4db42a8c9ae4d3d11aae89fa4fd797eca4614fbfd64d1d
    Args:
        tx_info_path:
        api_url:

    Returns:

    """
    cmd = f"export API_URL={api_url} && " \
          f"rm -rf /tmp/migrations && " \
          f"mkdir /tmp/migrations && " \
          f"{cli_path} deploy apply-txs --migration-dir /tmp/migrations --info-file {tx_info_path}" \
          f" --output-format json | grep -v transaction"
    return json.loads(run_command(cmd))


def util_key_info_by_private_key(account_private):
    """
    MacBook-Pro-4 0.111.0 % echo 0xd00c06bfd800d27397002dca6fb0993d5ba6399b4238b2f29ee9deb97593d2bc >
    tmp.data && ./ckb-cli util key-info --privkey-path tmp.data --output-format json && rm tmp.data

    Put this config in < ckb.toml >:

    [block_assembler]
    code_hash = "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8"
    hash_type = "type"
    args = "0xc8328aabcd9b9e8e64fbc566c4385c3bdeb219d7"
    message = "0x"

    {
      "address": {
        "mainnet": "ckb1qzda0cr08m85hc8jlnfp3zer7xulejywt49kt2rr0vthywaa50xwsqwgx292hnvmn68xf779vmzrshpmm6epn4cp2rpz9",
        "testnet": "ckt1qzda0cr08m85hc8jlnfp3zer7xulejywt49kt2rr0vthywaa50xwsqwgx292hnvmn68xf779vmzrshpmm6epn4c0cgwga"
      },
      "address(deprecated)": {
        "mainnet": "ckb1qyqvsv5240xeh85wvnau2eky8pwrhh4jr8ts6f6daz",
        "testnet": "ckt1qyqvsv5240xeh85wvnau2eky8pwrhh4jr8ts8vyj37"
      },
      "lock_arg": "0xc8328aabcd9b9e8e64fbc566c4385c3bdeb219d7",
      "lock_hash": "0x32e555f3ff8e135cece1351a6a2971518392c1e30375c1e006ad0ce8eac07947",
      "old-testnet-address": "ckt1q9gry5zgeqeg427dnw0gue8mc4nvgwzu800tyxwh7kdvf8",
      "pubkey": "03fe6c6d09d1a0f70255cddf25c5ed57d41b5c08822ae710dc10f8c88290e0acdf"
    }
    :param account_private:  private key
    :return: json for account msg
    """
    # echo 0xd00c06bfd800d27397002dca6fb0993d5ba6399b4238b2f29ee9deb97593d2bc > tmp.data && ./ckb-cli util key-info
    # --privkey-path tmp.data --output-format json && rm tmp.data
    cmd = f"echo {account_private} > /tmp/tmp.data && {cli_path} util key-info --privkey-path /tmp/tmp.data " \
          f"--output-format json"
    return json.loads(run_command(cmd))


def tx_init(tx_file, api_url="http://127.0.0.1:8114"):
    """
    ./ckb-cli tx init --tx-file tx.txt
    status: success
    MacBook-Pro-4 0.111.0 % cat tx.txt
    {
      "transaction": {
        "version": "0x0",
        "cell_deps": [],
        "header_deps": [],
        "inputs": [],
        "outputs": [],
        "outputs_data": [],
        "witnesses": []
      },
      "multisig_configs": {},
      "signatures": {}
    }%
    Args:
        api_url: default ckb rpc url
        tx_file:

    Returns:
    """
    cmd = f"export API_URL={api_url} && {cli_path} tx init --tx-file {tx_file}"
    return run_command(cmd)


def tx_sign_inputs(account_private, tx_file, api_url="http://127.0.0.1:8114"):
    """

    Args:
        account_private:
        tx_file:
        api_url:

    Returns:
        lock-arg: 0x9e2578fd0679a24726b7930fffb99a721c26f8db3d00000000010020
        signature: 0x0c44c12638277ffa6eafeac55cd918932f1cdbcfd4df413c11e8fb5
        b48f41ba22f738bad494e63d78c2bf2a4e0f4676db1d48d37f3d872d28bac70b2ef5a567a01
    """
    cmd = f"export API_URL={api_url} && echo {account_private} > /tmp/account.demo && {cli_path} tx sign-inputs " \
          f"--privkey-path /tmp/account.demo --tx-file {tx_file} --output-format json && rm /tmp/account.demo"
    return json.loads(run_command(cmd))


def tx_add_signature(lock_arg, signature, tx_file, api_url="http://127.0.0.1:8114"):
    cmd = f"export API_URL={api_url} && {cli_path} tx add-signature --lock-arg {lock_arg} --signature {signature} " \
          f"--tx-file {tx_file}"
    return run_command(cmd)


def tx_send(tx_file, api_url="http://127.0.0.1:8114"):
    cmd = f"export API_URL={api_url} && {cli_path} tx send --tx-file {tx_file}"
    return run_command(cmd)


def tx_add_input(tx_hash, index, tx_file, api_url="http://127.0.0.1:8114"):
    """
    add input and sign dep
    Args:
        tx_hash:
        index:
        tx_file:

    Returns:

    """
    cmd = f"export API_URL={api_url} && {cli_path} tx add-input --tx-hash {tx_hash} --index {index} --tx-file {tx_file}"
    return run_command(cmd)


def tx_add_multisig_config(ckb_address, tx_file, api_url="http://127.0.0.1:8114"):
    """
    ./ckb-cli tx add-multisig-config --sighash-address ckt1qyqdfjzl8ju2vfwjtl4mttx6me09hayzfldq8m3a0y --tx-file tx.txt
    status: success
    MacBook-Pro-4 0.111.0 % cat tx.txt
    {
      "transaction": {
        "version": "0x0",
        "cell_deps": [],
        "header_deps": [],
        "inputs": [],
        "outputs": [],
        "outputs_data": [],
        "witnesses": []
      },
      "multisig_configs": {
        "0x9e2578fd0679a24726b7930fffb99a721c26f8db": {
          "sighash_addresses": [
            "ckt1qyqdfjzl8ju2vfwjtl4mttx6me09hayzfldq8m3a0y"
          ],
          "require_first_n": 0,
          "threshold": 1
        }
      },
      "signatures": {}
    }%
        Args:
            api_url:
            ckb_address:
            tx_file:

        Returns:

    """
    cmd = f"export API_URL={api_url} && {cli_path} tx add-multisig-config --sighash-address  {ckb_address} " \
          f"--tx-file {tx_file}"
    return run_command(cmd)


def tx_info(tx_file_path, api_url="http://127.0.0.1:8114"):
    cmd = f"export API_URL={api_url} && {cli_path} tx info --tx-file {tx_file_path}"
    return run_command(cmd)


def tx_add_type_out_put(code_hash, hash_type, arg, capacity_hex, out_put_data, tx_file):
    with open(tx_file, "r") as file:
        tx_info_str = file.read()

    with open(tx_file, "w") as f:
        tx = json.loads(tx_info_str)
        tx["transaction"]["outputs"].append({
            "capacity": capacity_hex,
            "lock": {
                "code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
                "hash_type": "type",
                "args": "0xc8328aabcd9b9e8e64fbc566c4385c3bdeb219d5"
            },
            "type": {
                "code_hash": code_hash,
                "hash_type": hash_type,
                "args": arg
            }
        })
        tx["transaction"]["outputs_data"].append(out_put_data)

        tx_info_str = json.dumps(tx, indent=4)
        f.write(tx_info_str)


def tx_add_cell_dep(tx_hash, index_hex, tx_file):
    with open(tx_file, "r") as file:
        tx_info_str = file.read()

    with open(tx_file, "w") as f:
        tx = json.loads(tx_info_str)
        tx["transaction"]["cell_deps"].insert(0,
            {
                "out_point": {
                    "tx_hash": tx_hash,
                    "index": index_hex
                },
                "dep_type": "code"
            }
        )
        tx_info_str = json.dumps(tx, indent=4)
        f.write(tx_info_str)


def get_deploy_toml_config(account_private, contract_bin_path, enable_type_id):
    # get account script
    account = util_key_info_by_private_key(account_private)
    # return format toml
    return f"""
    [[cells]]
name = "compact_udt_lock"
enable_type_id = {str(enable_type_id).lower()}
location = {{ file = "{contract_bin_path}" }}

[[dep_groups]]
name = "my_dep_group"
cells = []

[lock]
code_hash = "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8"
args = "{account["lock_arg"]}"
hash_type = "type"
    """
