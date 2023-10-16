from test_cases.rpc.node_fixture import get_cluster


class TestGenerateEpochs:

    def test_generate_epochs(self, get_cluster):
        cluster = get_cluster
        tip_number = cluster.ckb_nodes[0].getClient().get_tip_block_number()
        pre_epoch = cluster.ckb_nodes[0].getClient().get_current_epoch()
        print("pre epoch:", pre_epoch)

        result = cluster.ckb_nodes[0].getClient().generate_epochs("0x2")
        current_tip_number = cluster.ckb_nodes[0].getClient().get_tip_block_number()
        epoch = cluster.ckb_nodes[0].getClient().get_current_epoch()
        print("current epoch:", epoch)
        assert "0x" in result
        assert tip_number < current_tip_number
        assert int(pre_epoch['number'], 16) + 2 == int(epoch['number'], 16)