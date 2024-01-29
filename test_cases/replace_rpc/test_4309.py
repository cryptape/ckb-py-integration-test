from framework.basic import CkbTest
from framework.util import run_command


class Test4309(CkbTest):

    @classmethod
    def setup_class(cls):
        cls.node113 = cls.CkbNode.init_dev_by_port(cls.CkbNodeConfigPath.CURRENT_TEST, "telnet/node", 8114, 8115)
        cls.node113.prepare()
        cls.node113.start()

    @classmethod
    def teardown_class(cls):
        print("teardown_class")
        cls.node113.stop()
        cls.node113.clean()

    def test_4309(self):
        """
        https://github.com/nervosnetwork/ckb/issues/4309
        """
        ret = run_command(
            """curl -s -X GET http://127.0.0.1:8114 -H 'Content-Type: application/json' -d '{ "id": 42, "jsonrpc": 
            "2.0", "method": "sync_state", "params": [ ] }'""")
        assert "Used HTTP Method is not allowed. POST or OPTIONS is required" in ret
