import json
import time

from framework.basic import CkbTest


class TestTelnetAndWebsocket(CkbTest):

    @classmethod
    def setup_class(cls):
        cls.node113 = cls.CkbNode.init_dev_by_port(cls.CkbNodeConfigPath.CURRENT_TEST, "telnet/node", 8119, 8129)
        cls.node113.prepare(
            other_ckb_config={
                "ckb_logger_filter": "debug",
                "ckb_tcp_listen_address": "127.0.0.1:18116",
                "ckb_ws_listen_address": "127.0.0.1:18124"})
        cls.node112 = cls.CkbNode.init_dev_by_port(cls.CkbNodeConfigPath.V112, "telnet/node2", 8126, 8127)
        cls.node112.prepare(other_ckb_config={
            "ckb_logger_filter": "debug",
            "ckb_tcp_listen_address": "127.0.0.1:18115",
            "ckb_ws_listen_address": "127.0.0.1:18125"})
        cls.node112.start()
        cls.node113.start()
        cls.node112.connected(cls.node113)
        cls.Miner.make_tip_height_number(cls.node113, 100)
        cls.Node.wait_node_height(cls.node112, 100, 1000)

    @classmethod
    def teardown_class(cls):
        cls.node112.stop()
        cls.node112.clean()

        cls.node113.stop()
        cls.node113.clean()

    def test_01_sub_tip_block_number(self):
        telnet_new_tip_header_112 = self.node112.subscribe_telnet("new_tip_header")
        telnet_new_tip_header_113 = self.node113.subscribe_telnet("new_tip_header")
        ws_new_tip_header_112 = self.node112.subscribe_websocket("new_tip_header")
        ws_new_tip_header_113 = self.node113.subscribe_websocket("new_tip_header")
        for i in range(10):
            self.Miner.miner_with_version(self.node112, "0x0")
            telnet_new_tip_header_112_ret = telnet_new_tip_header_112.read_very_eager()
            ws_new_tip_header_112_ret = ws_new_tip_header_112.recv()
            telnet_new_tip_header_113_ret = telnet_new_tip_header_113.read_very_eager()
            ws_new_tip_header_113_ret = ws_new_tip_header_113.recv()
            print("telnet_new_tip_header_113_ret:",
                  json.loads(telnet_new_tip_header_113_ret.decode())['params']['result'])
            print("ws_new_tip_header_113_ret:", json.loads(ws_new_tip_header_113_ret)['params']['result'])
            assert json.loads(telnet_new_tip_header_113_ret.decode())['params']['result'] == \
                   json.loads(ws_new_tip_header_113_ret)['params']['result']
            # print("telnet_new_tip_header_112_ret:",
            #       json.loads(telnet_new_tip_header_112_ret.decode())['params']['result'])
            # assert json.loads(telnet_new_tip_header_112_ret.decode())['params']['result'] == \
            # json.loads(telnet_new_tip_header_113_ret.decode())['params']['result']
            print("ws_new_tip_header_112_ret:", json.loads(ws_new_tip_header_112_ret)['params']['result'])
            assert json.loads(ws_new_tip_header_112_ret)['params']['result'] == \
                   json.loads(ws_new_tip_header_113_ret)['params']['result']
        telnet_new_tip_header_112.close()
        telnet_new_tip_header_113.close()
        ws_new_tip_header_112.close()
        ws_new_tip_header_113.close()

    def test_02_sub_new_tip_block(self):
        telnet_new_tip_block_112 = self.node112.subscribe_telnet("new_tip_block")
        telnet_new_tip_block_113 = self.node113.subscribe_telnet("new_tip_block")
        ws_new_tip_block_112 = self.node112.subscribe_websocket("new_tip_block")
        ws_new_tip_block_113 = self.node113.subscribe_websocket("new_tip_block")
        for i in range(10):
            self.Miner.miner_with_version(self.node112, "0x0")
            telnet_new_tip_block_112_ret = telnet_new_tip_block_112.read_very_eager()
            ws_new_tip_block_112_ret = ws_new_tip_block_112.recv()
            telnet_new_tip_block_113_ret = telnet_new_tip_block_113.read_very_eager()
            ws_new_tip_block_113_ret = ws_new_tip_block_113.recv()
            # print("telnet_new_tip_block_112_ret:", json.loads(telnet_new_tip_block_112_ret)['params']['result'])
            print("ws_new_tip_block_112_ret:", json.loads(ws_new_tip_block_112_ret)['params']['result'])
            print("telnet_new_tip_block_113_ret:", json.loads(telnet_new_tip_block_113_ret)['params']['result'])
            print("ws_new_tip_block_113_ret:", json.loads(ws_new_tip_block_113_ret)['params']['result'])
            assert json.loads(ws_new_tip_block_112_ret)['params']['result'] == \
                   json.loads(telnet_new_tip_block_113_ret)['params']['result']
            assert json.loads(ws_new_tip_block_112_ret)['params']['result'] == \
                   json.loads(ws_new_tip_block_113_ret)['params']['result']
        telnet_new_tip_block_112.close()
        telnet_new_tip_block_113.close()
        ws_new_tip_block_112.close()
        ws_new_tip_block_113.close()

    def test_03_sub_new_tx(self):
        telnet_new_tx_112 = self.node112.subscribe_telnet("new_transaction")
        ws_new_tx_112 = self.node112.subscribe_websocket("new_transaction")
        telnet_new_tx_113 = self.node113.subscribe_telnet("new_transaction")
        ws_new_tx_113 = self.node113.subscribe_websocket("new_transaction")
        account1 = self.Ckb_cli.util_key_info_by_private_key(self.Config.ACCOUNT_PRIVATE_1)

        for i in range(1):
            tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(
                self.Config.MINER_PRIVATE_1,
                account1['address']['testnet'],
                140,
                self.node113.client.url)
            self.Miner.miner_until_tx_committed(self.node113, tx_hash)
            telnet_new_tx_113_ret = telnet_new_tx_113.read_very_eager()
            telnet_new_tx_112_ret = telnet_new_tx_112.read_very_eager()
            ws_new_tx_113_ret = ws_new_tx_113.recv()
            ws_new_tx_112_ret = ws_new_tx_112.recv()
            print("telnet_new_tx_113_ret:", telnet_new_tx_113_ret)
            print("ws_new_tx_113_ret:", ws_new_tx_113_ret)
            # print("telnet_new_tx_112_ret:", telnet_new_tx_112_ret)
            print("ws_new_tx_112_ret:", ws_new_tx_112_ret)
            assert len(json.loads(telnet_new_tx_113_ret.decode())['params']['result']) == \
                   len(json.loads(ws_new_tx_113_ret)['params']['result'])
            assert len(json.loads(telnet_new_tx_113_ret.decode())['params']['result']) == \
                   len(json.loads(ws_new_tx_112_ret)['params']['result'])
        telnet_new_tx_112.close()
        ws_new_tx_112.close()
        telnet_new_tx_113.close()
        ws_new_tx_113.close()

    def test_04_sub_proposal_tx(self):
        telnet_new_tx_112 = self.node112.subscribe_telnet("proposed_transaction")
        ws_new_tx_112 = self.node112.subscribe_websocket("proposed_transaction")
        telnet_new_tx_113 = self.node113.subscribe_telnet("proposed_transaction")
        ws_new_tx_113 = self.node113.subscribe_websocket("proposed_transaction")
        account1 = self.Ckb_cli.util_key_info_by_private_key(self.Config.ACCOUNT_PRIVATE_1)
        for i in range(1):
            tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(
                self.Config.MINER_PRIVATE_1,
                account1['address']['testnet'],
                140,
                self.node113.client.url)

            self.Miner.miner_until_tx_committed(self.node113, tx_hash)
            telnet_new_tx_113_ret = telnet_new_tx_113.read_very_eager()
            telnet_new_tx_112_ret = telnet_new_tx_112.read_very_eager()
            ws_new_tx_113_ret = ws_new_tx_113.recv()
            ws_new_tx_112_ret = ws_new_tx_112.recv()
            print("telnet_new_tx_113_ret:", telnet_new_tx_113_ret)
            print("ws_new_tx_113_ret:", ws_new_tx_113_ret)
            # print("telnet_new_tx_112_ret:", telnet_new_tx_112_ret)
            print("ws_new_tx_112_ret:", ws_new_tx_112_ret)
            print("json:", json.loads(telnet_new_tx_113_ret.decode())['params']['result'])
            assert len(json.loads(telnet_new_tx_113_ret.decode())['params']['result']) == \
                   len(json.loads(ws_new_tx_113_ret)['params']['result'])
            assert len(json.loads(telnet_new_tx_113_ret.decode())['params']['result']) == \
                   len(json.loads(ws_new_tx_112_ret)['params']['result'])
        telnet_new_tx_112.close()
        ws_new_tx_112.close()
        telnet_new_tx_113.close()
        ws_new_tx_113.close()

    def test_05_reject_tx(self):
        telnet_new_tx_112 = self.node112.subscribe_telnet("rejected_transaction")
        ws_new_tx_112 = self.node112.subscribe_websocket("rejected_transaction")
        telnet_new_tx_113 = self.node113.subscribe_telnet("rejected_transaction")
        ws_new_tx_113 = self.node113.subscribe_websocket("rejected_transaction")
        account1 = self.Ckb_cli.util_key_info_by_private_key(self.Config.ACCOUNT_PRIVATE_1)
        for i in range(1):
            tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(
                self.Config.MINER_PRIVATE_1,
                account1['address']['testnet'],
                151,
                self.node113.client.url)
            time.sleep(3)
            tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(
                self.Config.MINER_PRIVATE_1,
                account1['address']['testnet'],
                151000,
                self.node113.client.url, "10000")

            tx_hash = self.Ckb_cli.wallet_transfer_by_private_key(
                self.Config.MINER_PRIVATE_1,
                account1['address']['testnet'],
                151000,
                self.node113.client.url, "100000")

            ws_new_tx_113_ret = ws_new_tx_113.recv()
            print("ws_new_tx_113_ret:", ws_new_tx_113_ret)

            telnet_new_tx_113_ret = telnet_new_tx_113.read_very_eager()
            print("telnet_new_tx_113_ret:", telnet_new_tx_113_ret)

            # telnet_new_tx_112_ret = telnet_new_tx_112.read_very_eager()
            # print("telnet_new_tx_112_ret:", telnet_new_tx_112_ret)

            ws_new_tx_112_ret = ws_new_tx_112.recv()
            print("ws_new_tx_112_ret:",ws_new_tx_112_ret)

            # assert len(json.loads(telnet_new_tx_113_ret.decode())['params']['result']) == \
            #        len(json.loads(ws_new_tx_113_ret)['params']['result'])
            # assert len(json.loads(telnet_new_tx_113_ret.decode())['params']['result']) == \
            #        len(json.loads(ws_new_tx_112_ret)['params']['result'])
        telnet_new_tx_112.close()
        ws_new_tx_112.close()
        telnet_new_tx_113.close()
        ws_new_tx_113.close()
        pass

    # //{"id": 2, "jsonrpc": "2.0", "method": "subscribe", "params": ["new_tip_block"]}
    # def test_sub_max_11(self):
    #     topic = "new_tip_block"
    #
    #     topic_str = '{"id": 2, "jsonrpc": "2.0", "method": "subscribe", "params": ["' + topic + '"]}'
    #     # topic_str = ''
    #     # for i in range(1):
    #     #     topic_str = topic_str+topic_str1 + "\n"
    #     tns = []
    #     for i in range(1000):
    #         tn = self.node113.subscribe_telnet("new_tip_block")
    #         tns.append(tn)
    #     for i in range(10000000):
    #         for tn in tns:
    #             tn.write(topic_str.encode('utf-8') + b"\n")
    #             # data = tn.read_until(b'}\n')
    #             # print(str(i) + ":", data)
    #             print("i:", i)
