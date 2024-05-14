import queue
import threading

from framework.basic import CkbTest
from framework.helper.loop_contract import LoopContract


class TestDemo(CkbTest):

    @classmethod
    def setup_class(cls):
        nodes = [
            cls.CkbNode.init_dev_by_port(cls.CkbNodeConfigPath.v117,
                                         "feature/gene_rate_epochs/node{i}".format(i=i), 8114 + i,
                                         8225 + i)
            for
            i in range(0, 2)]
        nodes.append(cls.CkbNode.init_dev_by_port(cls.CkbNodeConfigPath.v116,
                                                  "feature/gene_rate_epochs/node2".format(i=2), 8114 + 2,
                                                  8225 + 2))
        cls.cluster = cls.Cluster(nodes)
        cls.cluster.prepare_all_nodes()
        cls.cluster.start_all_nodes()
        cls.Miner.make_tip_height_number(nodes[0], 100)
        cls.cluster.connected_all_nodes()
        cls.Node.wait_cluster_height(cls.cluster, 100, 1000)

    @classmethod
    def teardown_class(cls):
        print("\nTeardown TestClass1")
        cls.cluster.stop_all_nodes()
        cls.cluster.clean_all_nodes()

    def test_01(self):
        print("----begin----")
        self.loop_contract = LoopContract()
        self.loop_contract.deploy(self.Config.ACCOUNT_PRIVATE_1, self.cluster.ckb_nodes[0])

        code_tx_hash, code_tx_index = self.loop_contract.get_deploy_hash_and_index()
        # ,"cpu_1yi_cycle","cpu_2yi_cycle","cpu_4yi_cycle","cpu_8yi_cycle","cpu_16yi_cycle"
        for method in ["cpu_5000w_cycle","cpu_1yi_cycle","cpu_2yi_cycle","cpu_4yi_cycle","cpu_8yi_cycle","cpu_16yi_cycle"]:
            invoke_arg, invoke_data = self.loop_contract.get_arg_and_data(method)
            tip_block_number = self.cluster.ckb_nodes[0].getClient().get_tip_block_number()
            print('tip_block_number:', tip_block_number)

            tx = self.Contract.build_invoke_ckb_contract(self.Config.MINER_PRIVATE_1,
                                                         code_tx_hash,
                                                         code_tx_index,
                                                         invoke_arg,
                                                         "type",
                                                         invoke_data,
                                                         api_url=self.cluster.ckb_nodes[0].getClient().url)

            tx2 = self.Contract.build_invoke_ckb_contract(self.Config.ACCOUNT_PRIVATE_2,
                                                          code_tx_hash,
                                                          code_tx_index,
                                                          invoke_arg,
                                                          "type",
                                                          invoke_data,
                                                          api_url=self.cluster.ckb_nodes[0].getClient().url)

            results_queue = queue.Queue()
            results_queue2 = queue.Queue()
            self.cluster.ckb_nodes[0].getClient().test_tx_pool_accept(tx)
            self.cluster.ckb_nodes[0].getClient().test_tx_pool_accept(tx2)
            tx_threader = threading.Thread(target=send_transaction, args=(self.cluster.ckb_nodes[0], tx, results_queue))
            tx_threader2 = threading.Thread(target=send_transaction,
                                            args=(self.cluster.ckb_nodes[0], tx2, results_queue2))

            tx_threader.start()
            tx_threader2.start()
            for i in range(10):
                self.cluster.ckb_nodes[0].getClient().send_test_verify_action("suspend")
            ret = tx_threader.join(5)
            print("fist join ret:", results_queue.empty())
            assert results_queue.empty() == True
            num = 0
            while results_queue.empty() or results_queue2.empty():
                num += 1
                self.cluster.ckb_nodes[0].getClient().send_test_verify_action("suspend")
                self.cluster.ckb_nodes[0].getClient().send_test_verify_action("resume")
            tx_threader.join()
            tx_threader2.join()
            assert results_queue.empty() == False
            assert results_queue2.empty() == False

            hash1 = results_queue.get()
            hash2 = results_queue2.get()
            for hash in [hash1, hash2]:
                self.Node.wait_get_transaction(self.cluster.ckb_nodes[0], hash, "pending")
                self.Node.wait_get_transaction(self.cluster.ckb_nodes[2], hash, "pending")
                node1_tx_response = self.cluster.ckb_nodes[0].getClient().get_transaction(hash)
                node3_tx_response = self.cluster.ckb_nodes[2].getClient().get_transaction(hash)
                assert node1_tx_response['cycles'] == node3_tx_response['cycles']
            for hash in [hash1, hash2]:
                self.Miner.miner_until_tx_committed(self.cluster.ckb_nodes[0], hash)
                tip_block_number = self.cluster.ckb_nodes[0].getClient().get_tip_block_number()
                self.Node.wait_cluster_height(self.cluster, tip_block_number, 100)
                print("send_test_verify_action times:", num)


def send_transaction(ckb_node, tx, results_queue):
    try:
        tx_hash = ckb_node.getClient().send_transaction(tx)
    except:
        print("-- error ---")
    results_queue.put(tx_hash)
