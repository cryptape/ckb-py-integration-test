import pytest

from framework.basic import CkbTest
from framework.util import run_command


class TestRpc(CkbTest):

    @classmethod
    def setup_class(cls):
        cls.node113 = cls.CkbNode.init_dev_by_port(cls.CkbNodeConfigPath.CURRENT_TEST, "telnet/node", 8114, 8115)
        cls.node113.prepare(other_ckb_config={"ckb_tcp_listen_address": "127.0.0.1:18114",
                                              "ckb_ws_listen_address": "127.0.0.1:18124"})

        cls.node112 = cls.CkbNode.init_dev_by_port(cls.CkbNodeConfigPath.V112, "telnet/node2", 8116, 8117)
        cls.node112.prepare(other_ckb_config={"ckb_tcp_listen_address": "127.0.0.1:18115",
                                              "ckb_ws_listen_address": "127.0.0.1:18125"})
        cls.node112.start()
        cls.node113.start()
        cls.node112.connected(cls.node113)
        cls.Miner.make_tip_height_number(cls.node113, 100)

    @classmethod
    def teardown_class(cls):
        print("teardown_class")
        cls.node112.stop()
        cls.node112.clean()
        cls.node113.stop()
        cls.node113.clean()

    def test_without_header(self):
            """
            112: need  application/json
            113: not need
            """
            ret113 = run_command(
                """curl -X POST  -d '[{"jsonrpc": "2.0", "method": "ping_peers", "params": [], "id": "1"}]' """ + f"""{self.node113.rpcUrl}/ """)
            assert "null" in ret113
            ret = run_command(
                """curl -X POST  -d '[{"jsonrpc": "2.0", "method": "ping_peers", "params": [], "id": "1"}]' """ + f"""{self.node112.rpcUrl}/ """)
            assert "Content-Type: application/json is required" in ret

    def test_01_with_error(self):
        """
        {"id": 42, "jsonrpc": "2.0", "method": "get_block_by_number", "params": ["0", null, null]}
        112:{"jsonrpc": "2.0", "error": {"code": -32602, "message": "Invalid params: Invalid Uint64 0: without `0x` prefix."}, "id": 42}
        113:{"jsonrpc": "2.0", "error": {"code": -32602, "message": "Invalid parameter for `block_number`: Invalid Uint64 0: without `0x` prefix"}, "id": 42}
        """
        with pytest.raises(Exception) as exc_info:
            ret = self.node112.getClient().get_block_by_number("0")
        expected_error_message = "Invalid params: Invalid Uint64 0: without `0x` prefix"
        assert expected_error_message in exc_info.value.args[0], \
            f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

        with pytest.raises(Exception) as exc_info:
            ret = self.node113.getClient().get_block_by_number("0")
        expected_error_message = "Invalid parameter for `block_number`: Invalid Uint64 0: without `0x` prefix"
        assert expected_error_message in exc_info.value.args[0], \
            f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

        pass

    def test_01_with_error_2(self):
        """
        {"jsonrpc": "2.0", "method": "dry_run_transaction", "params": [{}], "id": "1"}
            112:{"jsonrpc": "2.0", "error": {"code": -32602, "message": "message":"Invalid params: missing field `version`."}, "id": 42}
            113:{"jsonrpc": "2.0", "error": {"code": -32602, "message": "message":"Invalid params: missing field `version`."}, "id": 42}
        """
        with pytest.raises(Exception) as exc_info:
            ret = self.node112.getClient().get_block_by_number("0")
        expected_error_message = "Invalid params: Invalid Uint64 0: without `0x` prefix"
        assert expected_error_message in exc_info.value.args[0], \
            f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

        with pytest.raises(Exception) as exc_info:
            ret = self.node113.getClient().get_block_by_number("0")
        expected_error_message = ""
        assert expected_error_message in exc_info.value.args[0], \
            f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"


    @pytest.mark.skip
    def test_max_response(self):
        """
        batch get_block_by_number count:922
        112: successful
        113: successful
        batch get_block_by_number count:923
        112:failed
        113:failed
        """
        # 测试返回数据上限
        rpcUrls = [self.node112.rpcUrl, self.node113.rpcUrl]
        for rpcUrl in rpcUrls:
            requestBody = ""
            for i in range(922):
                requestBody = requestBody + """{"jsonrpc": "2.0", "method": "get_block_by_number", "params": ["0x0"], 
                "id": "1"},"""
            requestBody = requestBody[:-1]
            requests = """curl -vvv -X POST -H "Content-Type: application/json" -d '[""" + str(
                requestBody) + f"""]' {rpcUrl} > /tmp/null"""
            run_command(requests)
            run_command("rm -rf /tmp/null")

        for rpcUrl in rpcUrls:
            requestBody = ""
            for i in range(923):
                requestBody = requestBody + """{"jsonrpc": "2.0", "method": "get_block_by_number", "params": ["0x0"], 
                "id": "1"},"""
            requestBody = requestBody[:-1]
            requests = """curl -vvv -X POST -H "Content-Type: application/json" -d '[""" + str(
                requestBody) + f"""]' {rpcUrl} > /tmp/null"""
            with pytest.raises(Exception) as exc_info:
                run_command(requests)
            expected_error_message = "Empty reply from server"
            assert expected_error_message in exc_info.value.args[0], \
                f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

    @pytest.mark.skip
    def test_max_batch_count(self):
        """
        batch send count :15376
        112: successful
        113: successful
        batch send count :15377
        112: failed
        113: failed
        """
        rpcUrls = [
            self.node112.rpcUrl,
            self.node113.rpcUrl
        ]
        for rpcUrl in rpcUrls:
            requestBody = ""
            for i in range(15376):
                requestBody = requestBody + """{"jsonrpc": "2.0", "method": "ping_peers", "params": [], "id": "1"},"""
            requestBody = requestBody[:-1]
            requests = """curl -vvv -X POST -H "Content-Type: application/json" -d '[""" + str(
                requestBody) + f"""]' {rpcUrl}"""
            run_command(requests)
            for i in range(15378):
                requestBody = requestBody + """{"jsonrpc": "2.0", "method": "ping_peers", "params": [], "id": "1"},"""
            requestBody = requestBody[:-1]
            requests = """curl -vvv -X POST -H "Content-Type: application/json" -d '[""" + str(
                requestBody) + f"""]' {rpcUrl}"""

            with pytest.raises(Exception) as exc_info:
                run_command(requests)
            expected_error_message = "Argument list too long"
            assert expected_error_message in exc_info.value.args[1], \
                f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

    def test_websocket(self):
        """
        not support websocket
        112: not support,Handshake status 405 Method Not Allowed
        113: not support,not allowed. POST or OPTIONS is required
        """
        #   112: not support,Handshake status 405 Method Not Allowed
        with pytest.raises(Exception) as exc_info:
            socket = self.node112.subscribe_websocket("new_tip_header", self.node112.rpcUrl.replace("http://", ""))
        expected_error_message = "Handshake status 405 Method Not Allowed"
        assert expected_error_message in exc_info.value.args[0], \
            f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

        # 113 support
        with pytest.raises(Exception) as exc_info:
            socket = self.node113.subscribe_websocket("new_tip_header", self.node113.rpcUrl.replace("http://", ""))

        expected_error_message = "not allowed. POST or OPTIONS is required"

        assert expected_error_message in exc_info.value.args[0], \
            f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

    def test_telnet(self):
        """
        support telnet
        112: not
        113: not
        """
        socket = self.node112.subscribe_telnet("new_tip_header", self.node112.rpcUrl.replace("http://", ""))
        with pytest.raises(Exception) as exc_info:
            socket.read_very_eager()
        expected_error_message = "telnet connection closed"
        assert expected_error_message in exc_info.value.args[0], \
            f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

        socket = self.node113.subscribe_telnet("new_tip_header", self.node113.rpcUrl.replace("http://", ""))
        with pytest.raises(Exception) as exc_info:
            socket.read_very_eager()
        expected_error_message = "telnet connection closed"
        assert expected_error_message in exc_info.value.args[0], \
            f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"