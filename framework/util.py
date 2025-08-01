from jinja2 import Environment, FileSystemLoader, select_autoescape
import subprocess
import time
import json
import toml
import os, re
import struct

import hashlib

from framework import segwit_addr as sa

H256_ZEROS = "0x0000000000000000000000000000000000000000000000000000000000000000"

U128_MIN_COMPATIBLE = 0  # Adjust according to your definition
U128_MAX_COMPATIBLE = 2**128 - 1
import random


def to_json(value):
    return json.dumps(value)


def to_remove_str(value):
    return value[1:-1]


# ckb config ,ckb miner config ,ckb spec config
def get_ckb_configs(p2p_port, rpc_port, spec='{ file = "dev.toml" }'):
    return (
        {
            # 'ckb_chain_spec': '{ bundled = "specs/mainnet.toml" }',
            "ckb_chain_spec": spec,
            "ckb_network_listen_addresses": [
                "/ip4/0.0.0.0/tcp/{p2p_port}".format(p2p_port=p2p_port)
            ],
            "ckb_rpc_listen_address": "127.0.0.1:{rpc_port}".format(rpc_port=rpc_port),
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
            ],
            "ckb_block_assembler_code_hash": "0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8",
            "ckb_block_assembler_args": "0x8883a512ee2383c01574a328f60eeccbb4d78240",
            "ckb_block_assembler_hash_type": "type",
            "ckb_block_assembler_message": "0x",
        },
        {
            "ckb_miner_rpc_url": "127.0.0.1:{rpc_port}".format(rpc_port=rpc_port),
            "ckb_chain_spec": spec,
        },
        {},
    )


def create_config_file(config_values, template_path, output_file):
    file_loader = FileSystemLoader(get_project_root())
    # 创建一个环境
    env = Environment(loader=file_loader, autoescape=select_autoescape(["html", "xml"]))
    # 添加新的过滤器
    env.filters["to_json"] = to_json
    env.filters["to_remove_str"] = to_remove_str
    # 加载模板
    template = env.get_template(template_path)

    if not os.path.exists(os.path.dirname(output_file)):
        os.makedirs(os.path.dirname(output_file))

    # 使用数据渲染模板
    output = template.render(**config_values)

    # 将渲染的模板写入文件
    with open(output_file, "w") as f:
        f.write(output)


def run_command(cmd, check_exit_code=True):
    if cmd[-1] == "&":
        cmd1 = "{cmd} echo $! > pid.txt".format(cmd=cmd)
        print("cmd:{cmd}".format(cmd=cmd1))

        process = subprocess.Popen(cmd1, shell=True)
        time.sleep(1)
        print("process PID:", process.pid)
        with open("pid.txt", "r") as f:
            pid = int(f.read().strip())
            print("PID:", pid)
            # pid is new shell
            # pid+1 = run cmd
            # result:       55456  13.6  0.2 409387712  34448   ??  R     4:22PM   0:00.05 ./ckb run --indexer
            #        55457   5.8  0.0 34411380   2784   ??  S     4:22PM   0:00.02 /bin/sh -c ps aux | grep ckb
            #        55459   0.0  0.0 33726716   1836   ??  R     4:22PM   0:00.01 grep ckb
            #        55455   0.0  0.0 438105996   1508   ??  S     4:22PM   0:00.01 \
            #        /bin/sh -c cd /Users/guopenglin/WebstormProjects/gp/ckb-py-integration-test/tmp/node/node && \
            #        ./ckb run --indexer > node.log 2>&1 & echo $! > pid.txt
            return pid + 1

    print("cmd:{cmd}".format(cmd=cmd))
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
    )
    stdout, stderr = process.communicate()
    exit_code = process.returncode

    if exit_code != 0:
        print("Command failed with exit code:", exit_code)
        if stderr:
            print("Error:", stderr.decode("utf-8"))
        if not check_exit_code:
            return exit_code
        raise Exception(stderr.decode("utf-8"))
    if stderr.decode("utf-8") != "" and stdout.decode("utf-8") != "":
        print("wain:{result}".format(result=stderr.decode("utf-8")))
        print("result:{result}".format(result=stdout.decode("utf-8")))
        return stdout.decode("utf-8")
    print("result:{result}".format(result=stdout.decode("utf-8")))
    return stdout.decode("utf-8")


def get_project_root():
    current_path = os.path.dirname(os.path.abspath(__file__))
    pattern = r"(.*ckb-py-integration-test)"
    matches = re.findall(pattern, current_path)
    if matches:
        root_dir = max(matches, key=len)
        return root_dir
    else:
        raise Exception("not found ckb-py-integration-test dir")


def read_toml_file(file_path):
    try:
        with open(file_path, "r") as file:
            toml_content = file.read()
            config = toml.loads(toml_content)
            return config
    except Exception as e:
        print(f"Error reading TOML file: {e}")
        return None


def to_big_uint128_le_compatible(num):
    if num < U128_MIN_COMPATIBLE:
        raise ValueError(f"u128 {num} too small")

    if num > U128_MAX_COMPATIBLE:
        raise ValueError(f"u128 {num} too large")

    buf = bytearray(16)

    for i in range(4):
        buf[i * 4 : i * 4 + 4] = struct.pack("<I", num & 0xFFFFFFFF)
        num >>= 32
    return "0x" + buf.hex()


def to_int_from_big_uint128_le(hex_str):
    # Strip the '0x' prefix if present
    if hex_str.startswith("0x"):
        hex_str = hex_str[2:]

    # Convert the hex string into a byte array (16 bytes for uint128)
    buf = bytearray.fromhex(hex_str)

    # Reverse the byte array to convert from little-endian to big-endian
    buf.reverse()

    # Convert the byte array into an integer
    result = int.from_bytes(buf, byteorder="big")
    print("to_int_from_big_uint128_le:", hex_str, " result ", result)

    return result


def ckb_hasher():
    return hashlib.blake2b(digest_size=32, person=b"ckb-default-hash")


def ckb_hash(message):
    hasher = ckb_hasher()
    hasher.update(bytes.fromhex(message.replace("0x", "")))
    return "0x" + hasher.hexdigest()


def ckb_hash_script(arg):
    arg = arg.replace("0x", "")
    pack_lock = f"0x490000001000000030000000310000009bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce80114000000{arg}"
    return ckb_hash(pack_lock)


def generate_random_preimage():
    hash_str = "0x"
    for _ in range(64):
        hash_str += hex(random.randint(0, 15))[2:]
    return hash_str


# ref: https://github.com/nervosnetwork/rfcs/blob/master/rfcs/0021-ckb-address-format/0021-ckb-address-format.md
FORMAT_TYPE_FULL = 0x00
FORMAT_TYPE_SHORT = 0x01
FORMAT_TYPE_FULL_DATA = 0x02
FORMAT_TYPE_FULL_TYPE = 0x04

CODE_INDEX_SECP256K1_SINGLE = 0x00
CODE_INDEX_SECP256K1_MULTI = 0x01
CODE_INDEX_ACP = 0x02

BECH32_CONST = 1
BECH32M_CONST = 0x2BC830A3


def decodeAddress(addr, network="mainnet"):
    hrp = {"mainnet": "ckb", "testnet": "ckt"}[network]
    hrpgot, data, spec = sa.bech32_decode(addr)
    if hrpgot != hrp or data == None:
        return False
    decoded = sa.convertbits(data, 5, 8, False)
    if decoded == None:
        return False
    payload = bytes(decoded)
    format_type = payload[0]
    if format_type == FORMAT_TYPE_FULL:
        ptr = 1
        code_hash = "0x" + payload[ptr : ptr + 32].hex()
        ptr += 32
        hash_type = payload[ptr : ptr + 1].hex()
        ptr += 1
        args = "0x" + payload[ptr:].hex()
        return ("full", code_hash, hash_type, args)
    elif format_type == FORMAT_TYPE_SHORT:
        code_index = payload[1]
        pk = "0x" + payload[2:].hex()
        return ("short", code_index, pk)
    elif format_type == FORMAT_TYPE_FULL_DATA or format_type == FORMAT_TYPE_FULL_TYPE:
        full_type = {FORMAT_TYPE_FULL_DATA: "Data", FORMAT_TYPE_FULL_TYPE: "Type"}[
            format_type
        ]
        ptr = 1
        code_hash = payload[ptr : ptr + 32].hex()
        ptr += 32
        args = payload[ptr:].hex()
        return ("deprecated full", full_type, code_hash, args)


if __name__ == "__main__":
    ret = to_big_uint128_le_compatible(100000)
    ret1 = to_int_from_big_uint128_le(ret)
    print(ret1)
