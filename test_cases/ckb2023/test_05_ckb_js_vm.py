from framework.basic import CkbTest
from framework.util import get_project_root


class TestCkbJsVm(CkbTest):
    cluster: CkbTest.Cluster
    ckb_js_vm_deploy_hash: str
    ckb_js_vm_codeHash: str

    @classmethod
    def setup_class(cls):
        """
        1. star 4 node in tmp/cluster/hardFork dir
        2. link ckb node each other
        3. deploy contract
        4. miner 1000 block
        5. deploy ckb-js-vm
        Returns:

        """

        # 1. star 4 node in tmp/cluster/hardFork dir
        nodes = [
            cls.CkbNode.init_dev_by_port(
                cls.CkbNodeConfigPath.CURRENT_TEST,
                "cluster1/hardFork/node{i}".format(i=i),
                8114 + i,
                8225 + i,
            )
            for i in range(1, 5)
        ]
        cls.cluster = cls.Cluster(nodes)
        cls.cluster.prepare_all_nodes()
        cls.cluster.start_all_nodes()

        # 2. link ckb node each other
        cls.cluster.connected_all_nodes()

        # 4. miner 1000 block
        cls.Miner.make_tip_height_number(cls.cluster.ckb_nodes[0], 1000)
        cls.Node.wait_cluster_height(cls.cluster, 1000, 100)

        # 5. deploy ckb-js-vm
        cls.ckb_js_vm_deploy_hash = cls.Contract.deploy_ckb_contract(
            cls.Config.MINER_PRIVATE_1,
            f"{get_project_root()}/source/contract/js_vm/ckb-js-vm",
            enable_type_id=False,
            api_url=cls.cluster.ckb_nodes[0].getClient().url,
        )
        cls.Miner.miner_until_tx_committed(
            cls.cluster.ckb_nodes[0], cls.ckb_js_vm_deploy_hash, with_unknown=True
        )
        ckb_js_vm_codeHash = cls.Contract.get_ckb_contract_codehash(
            cls.ckb_js_vm_deploy_hash,
            0,
            False,
            cls.cluster.ckb_nodes[0].getClient().url,
        )
        print("ckb_js_vm_codeHash:", ckb_js_vm_codeHash)

    @classmethod
    def teardown_class(cls):
        print("\nTeardown TestClass1")
        cls.cluster.stop_all_nodes()
        cls.cluster.clean_all_nodes()

    def test_01_deploy(self):
        invoke_hash = self.deploy_js_code(
            self.Config.ACCOUNT_PRIVATE_1,
            f"{get_project_root()}/source/contract/js_vm/spawn-code",
        )
        self.Miner.miner_until_tx_committed(
            self.cluster.ckb_nodes[0], invoke_hash, with_unknown=True
        )

    def deploy_js_code(self, account, code_path):
        js_code_deploy_hash = self.Contract.deploy_ckb_contract(
            account,
            code_path,
            enable_type_id=True,
            api_url=self.cluster.ckb_nodes[0].getClient().url,
        )
        self.Miner.miner_until_tx_committed(
            self.cluster.ckb_nodes[0], js_code_deploy_hash, with_unknown=True
        )
        js_code_hash = self.Contract.get_ckb_contract_codehash(
            js_code_deploy_hash, 0, True, self.cluster.ckb_nodes[0].getClient().url
        )

        js_code_hash = js_code_hash.replace("0x", "")
        return self.Contract.invoke_ckb_contract(
            account_private=account,
            contract_out_point_tx_hash=self.ckb_js_vm_deploy_hash,
            contract_out_point_tx_index=0,
            type_script_arg=f"0x0000{js_code_hash}01",
            data="0x1234",
            hash_type="data2",
            api_url=self.cluster.ckb_nodes[0].getClient().url,
            cell_deps=[{"tx_hash": js_code_deploy_hash, "index": "0x0"}],
        )
