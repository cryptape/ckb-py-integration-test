from framework.fiber_rpc import FiberRPCClient


class WasmFiber:

    def __init__(self, private_key, peer_id, type="devnet", debug=False):
        self.private_key = private_key
        self.peerId = peer_id
        self.type = type
        self.rppcClient = FiberRPCClient("http://localhost:9000")
        if debug:
            return
        if type == "testnet":
            self.rppcClient.call(
                "new_client",
                [
                    {
                        "privateKey": self.private_key,
                        "peerId": self.peerId,
                    }
                ],
            )
        elif type == "devnet":
            self.rppcClient.call(
                "new_client",
                [
                    {
                        "privateKey": self.private_key,
                        "peerId": self.peerId,
                        "devConfig": "dev-config.yml",
                    }
                ],
            )
        elif type == "devnet-watch-tower":
            self.rppcClient.call(
                "new_client",
                [
                    {
                        "privateKey": self.private_key,
                        "peerId": self.peerId,
                        "devConfig": "dev-config-watch-tower.yml",
                    }
                ],
            )

    def stop(self):
        self.rppcClient.call("stop", [])

    def start(self):
        self.rppcClient.call("start", [])

    def refresh(self):
        if self.type == "testnet":
            self.rppcClient.call(
                "refresh",
                [
                    {
                        "privateKey": self.private_key,
                        "peerId": self.peerId,
                    }
                ],
            )
        elif self.type == "devnet":
            self.rppcClient.call(
                "refresh",
                [
                    {
                        "privateKey": self.private_key,
                        "peerId": self.peerId,
                        "devConfig": "dev-config.yml",
                    }
                ],
            )
        elif self.type == "devnet-watch-tower":
            self.rppcClient.call(
                "refresh",
                [
                    {
                        "privateKey": self.private_key,
                        "peerId": self.peerId,
                        "devConfig": "dev-config-watch-tower.yml",
                    }
                ],
            )

    def get_client(self):
        return self.rppcClient

    def connect_peer(self, fiber):
        node_info = fiber.get_client().node_info()
        addresses = node_info["addresses"][0].split("/")
        addresses[4] = f"{int(addresses[4])}/ws"
        # peer_id = node_info["addresses"][1].split("/")[-1]
        # peer_info = node_info["addresses"][0][""]
        print(addresses)
        self.rppcClient.connect_peer(
            {
                "address": "/".join(addresses),
            }
        )
