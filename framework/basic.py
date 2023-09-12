from abc import ABC, abstractmethod

import framework.helper.miner
import framework.helper.ckb_cli
import framework.helper.contract
import framework.helper.node
import framework.helper.contract_util
import framework.test_node
import framework.test_light_client
import framework.test_cluster
import framework.helper
import framework.config

class CkbTest(ABC):

    Miner: framework.helper.miner = framework.helper.miner
    Ckb_cli: framework.helper.ckb_cli = framework.helper.ckb_cli
    Contract: framework.helper.contract = framework.helper.contract
    Contract_util: framework.helper.contract_util = framework.helper.contract_util
    Node: framework.helper.node = framework.helper.node
    Cluster: framework.test_cluster.Cluster = framework.test_cluster.Cluster
    CkbNode: framework.test_node.CkbNode = framework.test_node.CkbNode
    CkbNodeConfigPath: framework.test_node.CkbNodeConfigPath = framework.test_node.CkbNodeConfigPath
    CkbLightClientConfigPath:framework.test_light_client.CkbLightClientConfigPath = framework.test_light_client.CkbLightClientConfigPath
    CkbLightClientNode: framework.test_light_client = framework.test_light_client.CkbLightClientNode
    Config = framework.config


    @classmethod
    def setup_class(cls):
        print("\nSetup TestClass2")

    @classmethod
    def teardown_class(cls):
        print("\nTeardown TestClass2")

    @abstractmethod
    def setup_method(self, method):
        print("\nSetting up method", method.__name__)

    @abstractmethod
    def teardown_method(self, method):
        print("\nTearing down method", method.__name__)