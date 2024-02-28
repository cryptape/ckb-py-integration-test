import json
import time

import pytest

from framework.basic import CkbTest
from framework.util import run_command


class TestRpc(CkbTest):

    @classmethod
    def setup_class(cls):
        cls.node113 = cls.CkbNode.init_dev_by_port(cls.CkbNodeConfigPath.CURRENT_TEST, "telnet/node", 8114, 8115)
        cls.node113.prepare(other_ckb_config={
            "ckb_logger_filter": "debug",
            "ckb_tcp_listen_address": "127.0.0.1:18115",
            "ckb_ws_listen_address": "127.0.0.1:18124"
        })
        cls.node112 = cls.CkbNode.init_dev_by_port(cls.CkbNodeConfigPath.V112, "telnet/node2", 8116, 8117)
        cls.node112.prepare(other_ckb_config={
            "ckb_tcp_listen_address": "127.0.0.1:18114"
        })
        cls.node112.start()
        cls.node113.start()
        cls.node112.connected(cls.node113)
        cls.Miner.make_tip_height_number(cls.node113, 100)
        cls.Node.wait_node_height(cls.node112, 90, 1000)

    @classmethod
    def teardown_class(cls):
        cls.node112.stop()
        cls.node112.clean()

        cls.node113.stop()
        cls.node113.clean()

    def test_link_count_max(self):
        """
            link tcp
            112: 1022
            113: > 10234
        """
        telnets = []
        for i in range(1000):
            print(i)
            telnet = self.node112.subscribe_telnet("new_tip_header")
            telnets.append(telnet)

        self.Miner.miner_with_version(self.node112, "0x0")
        time.sleep(1)
        for i in range(len(telnets)):
            telnet = telnets[i]
            ret = telnet.read_very_eager()
            print(ret)
            print(i, ':', len(ret))
            assert len(ret) > 700
            telnet.close()

        # test 113 max link count
        telnets = []
        for i in range(10000):
            print(i)
            telnet = self.node113.subscribe_telnet("new_tip_header")
            telnets.append(telnet)

        self.Miner.miner_with_version(self.node113, "0x0")
        for i in range(len(telnets)):
            telnet = telnets[i]
            ret = telnet.read_very_eager()
            print(i, ':', len(ret))
            assert len(ret) > 700
            telnet.close()

    def test_link_time_max(self):
        """
        link time
        112: keep link
        113: keep link
        """
        telnet113 = self.node113.subscribe_telnet("new_tip_header")
        telnet112 = self.node112.subscribe_telnet("new_tip_header")

        for i in range(300):
            self.Miner.miner_with_version(self.node113, "0x0")
            print("current idx:", i)
            ret113 = telnet113.read_very_eager()
            ret112 = telnet112.read_very_eager()
            print(ret113)
            print(ret112)
            time.sleep(1)
        telnet113.close()
        telnet112.close()

    def test_link_websocket(self):
        """
        support websocket
        112: not support
        113: not support
        """
        with pytest.raises(Exception) as exc_info:
            socket = self.node112.subscribe_websocket("new_tip_header",
                                                      self.node112.ckb_config['ckb_tcp_listen_address'])
        expected_error_message = "invalid literal for int() with base 10"
        assert expected_error_message in exc_info.value.args[0], \
            f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

        with pytest.raises(Exception) as exc_info:
            socket = self.node113.subscribe_websocket("new_tip_header",
                                                      self.node113.ckb_config['ckb_tcp_listen_address'])
        expected_error_message = "invalid literal for int() with base 10"
        assert expected_error_message in exc_info.value.args[0], \
            f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

    def test_rpc(self):
        """
        support rpc
        112: not support
        113: not support
        """
        client = self.node112.getClient()
        client.url = f"http://{self.node112.ckb_config['ckb_tcp_listen_address']}"

        with pytest.raises(Exception) as exc_info:
            response = client.call("get_tip_block_number", [], 1)
        expected_error_message = "request time out"
        assert expected_error_message in exc_info.value.args[0], \
            f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

        client = self.node113.getClient()
        client.url = f"http://{self.node113.ckb_config['ckb_tcp_listen_address']}"

        with pytest.raises(Exception) as exc_info:
            response = client.call("get_tip_block_number", [], 1)
        expected_error_message = "request time out"
        assert expected_error_message in exc_info.value.args[0], \
            f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

    def test_stop_node_when_link_telnet(self):
        """
        stop ckb when socker is keep live
        112: stop successful
        113: stop successful
        """
        self.node112.restart()
        socket = self.node112.subscribe_telnet("new_tip_header")
        self.node112.stop()
        port = self.node112.ckb_config['ckb_tcp_listen_address'].split(":")[-1]
        ret = run_command(f"lsof -i:{port} | grep ckb", check_exit_code=False)
        assert "ckb" not in str(ret)
        socket.close()
        ret = run_command(f"lsof -i:{port} | grep ckb", check_exit_code=False)
        assert "ckb" not in str(ret)

        self.node113.restart()
        socket = self.node113.subscribe_telnet("new_tip_header")
        self.node113.stop()
        port = self.node113.ckb_config['ckb_tcp_listen_address'].split(":")[-1]
        ret = run_command(f"lsof -i:{port} | grep ckb", check_exit_code=False)
        assert "ckb" not in str(ret)
        socket.close()
        ret = run_command(f"lsof -i:{port} | grep ckb", check_exit_code=False)
        assert "ckb" not in str(ret)
        self.node112.restart()
        self.node113.restart()

    def test_unsubscribe(self):
        """
        subscribe topic 1
        unsubscribe topic 1
            unsubscribe successful
        """

        client = self.node113.getClient()
        client.url = f"http://{self.node113.ckb_config['ckb_rpc_listen_address']}"
        socket = self.node113.subscribe_telnet("new_tip_header")
        self.Miner.miner_with_version(self.node113, "0x0")
        ret = socket.read_very_eager()
        ret = json.loads(ret)
        print(ret['params']['subscription'])
        subscribe_str = '{"id": 2, "jsonrpc": "2.0", "method": "unsubscribe", "params": ["' + ret['params'][
            'subscription'] + '"]}'
        print("subscribe_str:", subscribe_str)
        socket.write(subscribe_str.encode('utf-8') + b"\n")
        data = socket.read_until(b'}\n')
        assert "true" in data.decode('utf-8')
        self.Miner.miner_with_version(self.node113, "0x0")
        ret = socket.read_very_eager()
        assert ret.decode('utf-8') == ""
