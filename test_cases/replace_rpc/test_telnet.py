import json
import time

import pytest

from framework.basic import CkbTest
from framework.util import run_command


class TestRpc(CkbTest):

    @classmethod
    def setup_class(cls):
        """
        1. start ckb node 112 and 113
        2. connect 112 and 113 p2p
        3. miner node height = 90
        Returns:

        """
        cls.node113 = cls.CkbNode.init_dev_by_port(
            cls.CkbNodeConfigPath.CURRENT_TEST, "telnet/node", 8114, 8115
        )
        cls.node113.prepare(
            other_ckb_config={
                "ckb_logger_filter": "debug",
                "ckb_tcp_listen_address": "0.0.0.0:18115",
                "ckb_ws_listen_address": "0.0.0.0:18124",
            }
        )

        cls.node113.start()
        cls.Miner.make_tip_height_number(cls.node113, 100)

    @classmethod
    def teardown_class(cls):
        """
        1. stop ckb 113 version
        2. clear ckb 113 dir
        Returns:

        """

        cls.node113.stop()
        cls.node113.clean()

    def test_link_count_max(self):
        """
        1.link tcp
        2.112: 1022
        3.113: > 10234
        4.test 113 max link count
        """
        # 1.test 113 max link count
        telnets = []
        for i in range(100):
            print(i)
            telnet = self.node113.subscribe_telnet("new_tip_header")
            telnets.append(telnet)

        self.Miner.miner_with_version(self.node113, "0x0")
        for i in range(len(telnets)):
            telnet = telnets[i]
            ret = telnet.read_very_eager()
            print(i, ":", len(ret))
            assert len(ret) > 700
            telnet.close()

    def test_link_time_max(self):
        """
        1. link time
        2. 112: keep link
        3. 113: keep link
        """
        telnet113 = self.node113.subscribe_telnet("new_tip_header")

        for i in range(30):
            self.Miner.miner_with_version(self.node113, "0x0")
            print("current idx:", i)
            ret113 = telnet113.read_very_eager()
            print(ret113)
            time.sleep(1)
        telnet113.close()

    def test_link_websocket(self):
        """
        1. support websocket
        2. 112: not support
        3. 113: not support
        4. assert invalid literal for int() with base 10
        """
        with pytest.raises(Exception) as exc_info:
            socket = self.node113.subscribe_websocket(
                "new_tip_header",
                self.node113.ckb_config["ckb_tcp_listen_address"].replace(
                    "0.0.0.0", "127.0.0.1"
                ),
            )
        expected_error_message = "invalid literal for int() with base 10"
        assert (
            expected_error_message in exc_info.value.args[0]
        ), f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

    def test_rpc(self):
        """
        support rpc
        2. 113: not support
        3. assert request time out
        """

        client = self.node113.getClient()
        client.url = f"http://{self.node113.ckb_config['ckb_tcp_listen_address'].replace('0.0.0.0','127.0.0.1')}"

        with pytest.raises(Exception) as exc_info:
            response = client.call("get_tip_block_number", [], 1)
        expected_error_message = "request time out"
        assert (
            expected_error_message in exc_info.value.args[0]
        ), f"Expected substring '{expected_error_message}' not found in actual string '{exc_info.value.args[0]}'"

    def test_stop_node_when_link_telnet(self):
        """
        stop ckb when socker is keep live
        2. 113: stop successful
        3. assert "ckb" not in ret
        """

        self.node113.restart()
        socket = self.node113.subscribe_telnet("new_tip_header")
        self.node113.stop()
        port = self.node113.ckb_config["ckb_tcp_listen_address"].split(":")[-1]
        ret = run_command(f"lsof -i:{port} | grep ckb", check_exit_code=False)
        assert "ckb" not in str(ret)
        socket.close()
        ret = run_command(f"lsof -i:{port} | grep ckb", check_exit_code=False)
        assert "ckb" not in str(ret)
        self.node113.restart()

    def test_unsubscribe(self):
        """
        1.subscribe topic 1
        2.unsubscribe topic 1
        3.unsubscribe successful
        4.assert socket.read_very_eager() return is null
        """

        client = self.node113.getClient()
        client.url = f"http://{self.node113.ckb_config['ckb_rpc_listen_address'].replace('0.0.0.0','127.0.0.1')}"
        socket = self.node113.subscribe_telnet("new_tip_header")
        self.Miner.miner_with_version(self.node113, "0x0")
        ret = socket.read_very_eager()
        ret = json.loads(ret)
        print(ret["params"]["subscription"])
        subscribe_str = (
            '{"id": 2, "jsonrpc": "2.0", "method": "unsubscribe", "params": ["'
            + ret["params"]["subscription"]
            + '"]}'
        )
        print("subscribe_str:", subscribe_str)
        socket.write(subscribe_str.encode("utf-8") + b"\n")
        data = socket.read_until(b"}\n")
        assert "true" in data.decode("utf-8")
        self.Miner.miner_with_version(self.node113, "0x0")
        ret = socket.read_very_eager()
        assert ret.decode("utf-8") == ""
