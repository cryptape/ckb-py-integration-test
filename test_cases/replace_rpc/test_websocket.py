import time

import pytest

from framework.basic import CkbTest
from framework.util import run_command


class TestWebsocket(CkbTest):

    @classmethod
    def setup_class(cls):
        """
        1.start ckb version 113 and 112
        2. connect ckb node 112 and 113 version
        3. miner node112 and 113 height = 100
        Returns:

        """
        cls.node113 = cls.CkbNode.init_dev_by_port(
            cls.CkbNodeConfigPath.CURRENT_TEST, "telnet2/node", 8114, 8115
        )
        cls.node113.prepare(
            other_ckb_config={
                "ckb_logger_filter": "debug",
                "ckb_tcp_listen_address": "0.0.0.0:18114",
                "ckb_ws_listen_address": "0.0.0.0:18124",
            }
        )
        cls.node112 = cls.CkbNode.init_dev_by_port(
            cls.CkbNodeConfigPath.V112, "telnet2/node2", 8116, 8117
        )
        cls.node112.prepare(
            other_ckb_config={
                "ckb_logger_filter": "debug",
                "ckb_tcp_listen_address": "127.0.0.1:18115",
                "ckb_ws_listen_address": "127.0.0.1:18125",
            }
        )
        cls.node112.start()
        cls.node113.start()
        cls.node112.connected(cls.node113)
        cls.Miner.make_tip_height_number(cls.node113, 100)
        cls.Node.wait_node_height(cls.node112, 100, 1000)

    @classmethod
    def teardown_class(cls):
        """
        1. stop node 112 and 113 version
        2. clear node 112 and 113 dir
        Returns:

        """
        cls.node112.stop()
        cls.node112.clean()

        cls.node113.stop()
        cls.node113.clean()

    def test_link_count_max(self):
        """
        1. link tcp
        2. 112: 1022
        3. 113: > 10234
        4. test 113 max link count
        """
        # test 112  max link count
        websockets = []
        for i in range(100):
            print(i)
            websocket = self.node112.subscribe_websocket("new_tip_header")
            websockets.append(websocket)

        self.Miner.miner_with_version(self.node112, "0x0")
        for i in range(len(websockets)):
            websocket = websockets[i]
            ret = websocket.recv()
            print(i, ":", len(ret))
            websocket.close()

        # test 113 max link count
        websockets = []
        for i in range(10000):
            print(i)
            websocket = self.node113.subscribe_websocket("new_tip_header")
            websockets.append(websocket)

        self.Miner.miner_with_version(self.node113, "0x0")
        for i in range(len(websockets)):
            websocket = websockets[i]
            ret = websocket.recv()
            print(i, ":", len(ret))
            websocket.close()

    def test_link_time_max(self):
        """
        1. link time
        2. 112: keep link
        3. 113: keep link
        """
        websocket112 = self.node112.subscribe_websocket("new_tip_header")
        websocket113 = self.node113.subscribe_websocket("new_tip_header")

        for i in range(300):
            self.Miner.miner_with_version(self.node113, "0x0")
            print("current idx:", i)
            ret112 = websocket112.recv()
            ret113 = websocket113.recv()
            print(ret112)
            assert len(ret112) > 0
            assert len(ret113) > 0
            print(ret113)
            time.sleep(1)
        websocket113.close()
        websocket112.close()

    def test_rpc(self):
        """
        1. support rpc
        2. 112: not support
        3. 113: support
        """
        client = self.node112.getClient()
        client.url = f"http://{self.node112.ckb_config['ckb_ws_listen_address']}"

        with pytest.raises(Exception) as exc_info:
            response = client.call("get_tip_block_number", [], 1)
        expected_error_message = "Expecting value: line 1 column 1"
        assert (
            expected_error_message in exc_info.value.args[0]
        ), f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

        client = self.node113.getClient()
        client.url = f"http://{self.node113.ckb_config['ckb_ws_listen_address'].replace('0.0.0.0','127.0.0.1')}"

        response = client.call("get_tip_block_number", [], 1)

        # with pytest.raises(Exception) as exc_info:
        #     response = client.call("get_tip_block_number", [], 1)
        # expected_error_message = "request time out"
        # assert expected_error_message in exc_info.value.args[0], \
        #     f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

    def test_telnet(self):
        """
        1. assert telnet connection closed which 112 subscribe 113 node
        2. assert telnet connection closed which 113 subscribe 112 node
        Returns:

        """
        socket = self.node112.subscribe_telnet(
            "new_tip_header", self.node112.ckb_config["ckb_ws_listen_address"]
        )
        with pytest.raises(Exception) as exc_info:
            socket.read_very_eager()
        expected_error_message = "telnet connection closed"
        assert (
            expected_error_message in exc_info.value.args[0]
        ), f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

        socket = self.node113.subscribe_telnet(
            "new_tip_header", self.node112.ckb_config["ckb_ws_listen_address"]
        )
        with pytest.raises(Exception) as exc_info:
            socket.read_very_eager()
        expected_error_message = "telnet connection closed"
        assert (
            expected_error_message in exc_info.value.args[0]
        ), f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

    def test_stop_node_when_link_websocket(self):
        """
        1. stop ckb when socker is keep live
        2. 112: stop successful
        3. 113: stop failed
        """
        if self.skip_docker():
            pytest.skip("docker not support lsof")
            return
        self.node112.restart()
        socket = self.node112.subscribe_websocket("new_tip_header")
        self.node112.stop()
        port = self.node112.ckb_config["ckb_ws_listen_address"].split(":")[-1]
        ret = run_command(f"lsof -i:{port} | grep ckb", check_exit_code=False)
        assert "ckb" not in str(ret)
        socket.close()
        ret = run_command(f"lsof -i:{port} | grep ckb", check_exit_code=False)
        assert "ckb" not in str(ret)

        self.node113.restart()
        socket = self.node113.subscribe_websocket("new_tip_header")
        self.node113.stop()
        port = self.node113.ckb_config["ckb_ws_listen_address"].split(":")[-1]
        ret = run_command(f"lsof -i:{port} | grep ckb", check_exit_code=False)
        assert "ckb" not in str(ret)
        socket.close()
        ret = run_command(f"lsof -i:{port} | grep ckb", check_exit_code=False)
        assert "ckb" not in str(ret)
        self.node112.restart()
        self.node113.restart()
