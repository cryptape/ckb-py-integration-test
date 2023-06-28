import time


def make_tip_height_number(node, number):
    current_tip_number = node.getClient().get_tip_block_number()
    if current_tip_number == number:
        return
        # number < current_tip_number  cut block
    if number < current_tip_number:
        block_hash = node.getClient().get_block_hash(hex(number))
        node.getClient().truncate(block_hash)
        current_tip_number = node.getClient().get_tip_block_number()
        assert current_tip_number == number
        return
        # number >= current_tip_number miner block
    miner_num = number - current_tip_number
    # self.client.
    for i in range(miner_num):
        miner_with_version(node, "0x0")
    current_tip_number = node.getClient().get_tip_block_number()
    assert current_tip_number == number


def miner_until_tx_committed(node, tx_hash):
    for i in range(100):
        tx_response = node.getClient().get_transaction(tx_hash)
        if tx_response['tx_status']['status'] != "pending" and tx_response['tx_status']['status'] != "proposed":
            # miner_with_version(node, "0x0")
            return
        miner_with_version(node, "0x0")
        time.sleep(1)
    assert f"miner 100 block ,but tx_response always pending:{tx_hash}"


# https://github.com/nervosnetwork/rfcs/pull/416
# support > 0x0 when ckb2023 active
def miner_with_version(node, version):
    # get_block_template
    block = node.getClient().get_block_template()
    node.getClient().submit_block(block["work_id"], block_template_transfer_to_submit_block(block, version))
    pool = node.getClient().tx_pool_info()
    header = node.getClient().get_tip_header()
    print("miner block num:{number}".format(number=int(block['number'].replace("0x", ""), 16)))
    print("pool num:{pool_number}, header num:{header_number}".format(
        pool_number=int(pool["tip_number"].replace("0x", ""), 16),
        header_number=int(header["number"].replace("0x", ""), 16)))
    for i in range(100):
        pool_info = node.getClient().tx_pool_info()
        tip_number = node.getClient().get_tip_block_number()
        if int(pool_info["tip_number"],16) == tip_number:
            return
        time.sleep(1)
    raise Exception("pool_info not eq tip number")


def block_template_transfer_to_submit_block(block, version="0x0"):
    block['transactions'].insert(0, block['cellbase'])
    block['transactions'] = [x['data'] for x in block['transactions']]
    ret = {
        "header": {
            "compact_target": block["compact_target"],
            "dao": block["dao"],
            "epoch": block["epoch"],
            "extra_hash": "0x0000000000000000000000000000000000000000000000000000000000000000",
            "nonce": "0x0",
            "number": block["number"],
            "parent_hash": block["parent_hash"],
            "proposals_hash": "0x0000000000000000000000000000000000000000000000000000000000000000",
            "timestamp": get_hex_timestamp(),
            "transactions_root": "0x0000000000000000000000000000000000000000000000000000000000000000",
            "version": version,
        },
        "extension": block["extension"],
        "uncles": [],
        "transactions": block['transactions'],
        "proposals": block['proposals'],
    }
    return ret


def get_hex_timestamp():
    timestamp = int(time.time() * 1000)
    hex_timestamp = hex(timestamp)
    return hex_timestamp
