from framework.basic import CkbTest


class TestGenerateEpochs(CkbTest):

    @classmethod
    def setup_class(cls):
        nodes = [
            cls.CkbNode.init_dev_by_port(cls.CkbNodeConfigPath.CURRENT_TEST,
                                         "feature/gene_rate_epochs/node{i}".format(i=i), 8114 + i,
                                         8225 + i)
            for
            i in range(1, 5)]
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

    def test_01_generate_epochs_0x2(self):
        """
        调用generate_epochs 生成2个epoch 的number
        1. call generate_epochs generate 2 epoch
            return  0x...
            TODO : check 0x
        2. call  get_tip_block_number
                tip number > pre tip number
        3. call get_current_epoch
            epoch+= 2
        4. other nodes can sync
            sync successful
        """
        tip_number = self.cluster.ckb_nodes[0].getClient().get_tip_block_number()
        pre_epoch = self.cluster.ckb_nodes[0].getClient().get_current_epoch()
        print("pre epoch:", pre_epoch)

        result = self.cluster.ckb_nodes[0].getClient().generate_epochs("0x2")
        #  TODO  check generate_epochs result
        current_tip_number = self.cluster.ckb_nodes[0].getClient().get_tip_block_number()
        epoch = self.cluster.ckb_nodes[0].getClient().get_current_epoch()
        print("current epoch:", epoch)
        assert "0x" in result
        assert tip_number < current_tip_number
        assert int(pre_epoch['number'], 16) + 2 == int(epoch['number'], 16)
        self.Node.wait_cluster_height(self.cluster, current_tip_number, 1000)
