import time

import requests

import json


class FiberRPCClient:
    def __init__(self, url):
        self.url = url

    def send_btc(self, btc_pay_req):
        return self.call("send_btc", [btc_pay_req])

    def open_channel(self, param):
        """
        curl --location 'http://127.0.0.1:8227' --header 'Content-Type: application/json' --data '{
            "id": 42,
            "jsonrpc": "2.0",
            "method": "open_channel",
            "params": [
                {
                    "peer_id": "QmaQSn11jsAXWLhjHtZ9EVbauD88sCmYzty3GmYcoVWP2j",
                    "funding_amount": "0x2e90edd000"
                }
            ]
        }'
        {"jsonrpc": "2.0", "result": {"temporary_channel_id": "0xbf1b507e730b08024180ed9cb5bb3655606d3a89e94476033cf34d206d352751"}, "id": 42}
        """
        return self.call("open_channel", [param])

    def list_channels(self, param):
        """
        curl --location 'http://127.0.0.1:8227' --header 'Content-Type: application/json' --data '{
            "id": 42,
            "jsonrpc": "2.0",
            "method": "list_channels",
            "params": [
                {
                    "peer_id": "QmaQSn11jsAXWLhjHtZ9EVbauD88sCmYzty3GmYcoVWP2j"
                }
            ]
        }'
        {"jsonrpc": "2.0", "result": {"channels": [{"channel_id": "0x2329a1ced09d0c9eff46068ac939596bb657a984b1d6385db563f2de837b8879", "peer_id": "QmaQSn11jsAXWLhjHtZ9EVbauD88sCmYzty3GmYcoVWP2j", "state": {"state_name": "NEGOTIATING_FUNDING", "state_flags": "OUR_INIT_SENT | THEIR_INIT_SENT"}, "local_balance": "0x2d1f615200", "sent_tlc_balance": "0x0", "remote_balance": "0x0", "received_tlc_balance": "0x0", "created_at": "0x620a0b7b1676b"}]}, "id": 42}
        """
        return self.call("list_channels", [param])

    def accept_channel(self, param):
        return self.call("accept_channel", [param])

    def add_tlc(self, param):
        return self.call("add_tlc", [param])

    def remove_tlc(self, param):
        return self.call("remove_tlc", [param])

    def shutdown_channel(self, param):
        return self.call("shutdown_channel", [param])

    def new_invoice(self, param):
        return self.call("new_invoice", [param])

    def parse_invoice(self, param):
        return self.call("parse_invoice", [param])

    def connect_peer(self, param):
        return self.call("connect_peer", [param])

    def disconnect_peer(self, param):
        return self.call("disconnect_peer", [param])

    def send_payment(self, param):
        return self.call("send_payment", [param])

    def call(self, method, params):
        headers = {"content-type": "application/json"}
        data = {"id": 42, "jsonrpc": "2.0", "method": method, "params": params}
        print(
            "curl --location '{url}' --header 'Content-Type: application/json' --data '{data}'".format(
                url=self.url, data=json.dumps(data, indent=4)
            )
        )
        for i in range(100):
            try:
                response = requests.post(
                    self.url, data=json.dumps(data), headers=headers
                ).json()
                print("response:\n{response}".format(response=json.dumps(response)))
                if "error" in response.keys():
                    error_message = response["error"].get("message", "Unknown error")
                    raise Exception(f"Error: {error_message}")

                return response.get("result", None)
            except requests.exceptions.ConnectionError as e:
                print(e)
                print("request too quickly, wait 2s")
                time.sleep(2)
                continue
        raise Exception("request time out")
