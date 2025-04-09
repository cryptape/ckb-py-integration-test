import time
from framework.basic_fiber import FiberTest


class TestBuildRouter(FiberTest):
    """
    测试 build_router RPC 的功能：
    1. 基本路由构建
       - 测试指定 amount 和不指定 amount 的情况
       - 测试指定和不指定 final_tlc_expiry_delta 的情况

    2. 通道指定测试
       - 测试指定 channel_outpoint 的情况
       - 测试不指定 channel_outpoint 的情况（让算法自动选择通道）
       - 测试指定的 channel_outpoint 无效的情况

    3. 路径验证
       - 测试所有节点都存在的有效路径
       - 测试节点不存在的无效路径
       - 测试节点存在但无可用通道的情况

    4. 特殊情况
       - 测试空的 hops_info
       - 测试只有一个 hop 的情况
       - 测试包含重复节点的情况

    5. UDT 支付路由（可选）
       - 测试指定 udt 支付的情况
       - 测试 ckb 支付的情况
    """

    def test_base_build_router(self):
        """
        b-c-d-私-a网络
        1. d-a建立了路由关系，查看构建的路由返回信息
        """
        self.start_new_fiber(self.generate_account(10000))
        self.start_new_fiber(self.generate_account(10000))

        fiber1_balance = 1000 * 100000000
        fiber1_fee = 1000

        self.open_channel(self.fibers[1], self.fibers[2], 1000 * 100000000, 1)  # b-c
        self.open_channel(
            self.fibers[2], self.fibers[3], 1000 * 100000000, 1
        )  # c-d == b-c-d

        self.fibers[3].connect_peer(self.fibers[0])  # d-a
        time.sleep(1)
        self.fibers[3].get_client().open_channel(  # d -a private channel
            {
                "peer_id": self.fibers[0].get_peer_id(),
                "funding_amount": hex(fiber1_balance + 62 * 100000000),
                "tlc_fee_proportional_millionths": hex(fiber1_fee),
                "public": False,
            }
        )
        time.sleep(1)
        self.wait_for_channel_state(
            self.fibers[3].get_client(), self.fibers[0].get_peer_id(), "CHANNEL_READY"
        )
        # 查看d-a的channeloutpoint
        print(f"a peer_id:{self.fibers[0].get_peer_id()}")
        print(f"d peer_id:{self.fibers[3].get_peer_id()}")
        channels = (
            self.fibers[3]
            .get_client()
            .list_channels({"peer_id": self.fibers[0].get_peer_id()})
        )
        print(f"d-a,channel:{channels}")
        da_channel_outpoint = channels["channels"][0]["channel_outpoint"]
        print(f"d-a, channel_outpoint:{da_channel_outpoint}")

        router_hops = (
            self.fibers[3]
            .get_client()
            .build_router(
                {
                    "amount": hex(1 + 62 * 100000000),
                    "udt_type_script": None,
                    "hops_info": [
                        {
                            "pubkey": self.fibers[0]
                            .get_client()
                            .node_info()["node_id"],
                            "channel_outpoint": da_channel_outpoint,
                        },
                    ],
                    "final_tlc_expiry_delta": None,
                }
            )
        )
        print(f"router_hops:{router_hops}")
        hop = router_hops["router_hops"][0]
        print(f"hop:{hop}")
        assert hop["channel_outpoint"] == da_channel_outpoint
        assert hop["target"] == self.fibers[0].get_client().node_info()["node_id"]
        assert hop["amount_received"] == hex(1 + 62 * 100000000)
