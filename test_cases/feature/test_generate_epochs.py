from framework.basic import CkbTest
from framework.util import *


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
        cls.ckb_spec_config_dict = read_toml_file(get_project_root() + "/" + cls.cluster.ckb_nodes[0].ckb_config_path.ckb_spec_path)
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
        调用generate_epochs 生成2个epoch 的number;
        检验分母为0的情况，预期内部会把字母变成1，0x2会处理成0x10000000002
        1. call generate_epochs generate 2 epoch
            return  0x70800b4000002
            length在开头，708（16进制）就是1800;index在中间，为0xb4; number在最后，0x2
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
        epoch_info = parse_hex_string(result)
        print(f"Number: 0x{epoch_info.number():06X}")
        assert int(f"0x{epoch_info.number():06X}", 16) == int("0x2", 16)
        print(f"Index: 0x{epoch_info.index():04X}")
        print(f"Length: 0x{epoch_info.length():04X}")
        assert int(f"0x{epoch_info.length():04X}", 16) == self.ckb_spec_config_dict.get("params", {}).get("epoch_duration_target")/8
        current_tip_number = self.cluster.ckb_nodes[0].getClient().get_tip_block_number()
        epoch = self.cluster.ckb_nodes[0].getClient().get_current_epoch()
        print("current epoch:", epoch)
        assert "0x" in result
        assert tip_number < current_tip_number
        assert int(pre_epoch['number'], 16) + 2 == int(epoch['number'], 16)
        self.Node.wait_cluster_height(self.cluster, current_tip_number, 1000)


class EpochNumberWithFraction:
    def __init__(self, value):
        self.value = value

    def number(self):
        return (self.value >> 0) & ((1 << 24) - 1)

    def index(self):
        return (self.value >> 24) & ((1 << 16) - 1)

    def length(self):
        return (self.value >> 40) & ((1 << 16) - 1)

def parse_hex_string(hex_string):
    hex_string = hex_string[2:]
    if len(hex_string) < 12:
        return None
    value = int(hex_string, 16)
    return EpochNumberWithFraction(value)


