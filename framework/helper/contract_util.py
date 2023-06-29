from framework.test_node import CkbNode
from framework.helper.spawn_contract import SpawnContract
from framework.helper.contract import CKbContract
from framework.helper.miner import miner_with_version

def deploy_contracts(account_private, node: CkbNode) -> dict[str, CKbContract]:
    # if tip number < 10
    # miner to 10 block
    if node.getClient().get_tip_block_number() < 10:
        for i in range(10):
            miner_with_version(node, "0x0")
    # deploy contract
    spawn = SpawnContract()
    spawn.deploy(account_private, node)
    return {
        "SpawnContract": spawn
    }
