from framework.basic import CkbTest


class TestCkbPreview(CkbTest):

    @classmethod
    def setup_class(cls):
        cls.node = cls.CkbNode.init_dev_by_port(
            cls.CkbNodeConfigPath.PREVIEW_DUMMY,
            "preview/node{i}".format(i=1),
            8114,
            8225,
        )
        cls.node.prepare()
        cls.node.start()
        cls.Miner.make_tip_height_number(cls.node, 100)

    @classmethod
    def teardown_class(cls):
        print("\nTeardown TestClass1")
        cls.node.stop()
        cls.node.clean()

    def test_transfer_data2(self):
        txHash = self.Ckb_cli.wallet_transfer_by_private_key(
            self.Config.MINER_PRIVATE_1,
            "ckt1qp5usrt2syzfjj7acyetk45vj57kp7hq4jfg4ky8e9k7ss6v52neqpqh7xtq0",
            140,
            self.node.client.url,
        )
        self.Miner.miner_until_tx_committed(self.node, txHash)
