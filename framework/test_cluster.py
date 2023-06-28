from framework.test_node import CkbNode
import time
from typing import List


class Cluster:

    def __init__(self, ckb_nodes: List[CkbNode]):
        self.ckb_nodes: List[CkbNode] = ckb_nodes

    def add_node(self, node: CkbNode):
        self.ckb_nodes.append(node)

        for num in range(len(self.ckb_nodes) - 1):
            self.connected_node(num, len(self.ckb_nodes) - 1)

    def prepare_all_nodes(self):
        for node in self.ckb_nodes:
            node.prepare()

    def connected_node(self, num1, num2):
        self.ckb_nodes[num1].connected(self.ckb_nodes[num2])
        self.ckb_nodes[num2].connected(self.ckb_nodes[num1])

    def connected_all_nodes(self):
        for num in range(len(self.ckb_nodes)):
            for link_num in range(len(self.ckb_nodes)):
                self.connected_node(num, link_num)

    def disconnected_node(self, num1, num2):
        pass

    def remove_node(self, num1):
        pass

    def start_all_nodes(self):
        for node in self.ckb_nodes:
            node.start()
            # todo remove sleep
        time.sleep(3)

    def stop_all_nodes(self):
        for node in self.ckb_nodes:
            node.stop()

    def clean_all_nodes(self):
        for node in self.ckb_nodes:
            node.clean()

    def get_all_nodes_height(self):
        return [node.getClient().get_tip_block_number() for node in self.ckb_nodes]
