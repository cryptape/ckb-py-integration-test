from test_cases.rpc.node_fixture import get_cluster


class TestGeConsensus:

    def test_threshold_is_hex(self, get_cluster):
        """
        https://github.com/nervosnetwork/ckb/pull/3980/files
         "threshold":
         111<
         {
                        "denom": 4,
                        "numer": 3
             },

        >111
         "threshold": {
                        "denom": "0x4",
                        "numer": "0x3"
        },
        invoke rpc get_consensus
        - threshold return 0x...
        :return:
        """
        cluster = get_cluster
        consensus = cluster.ckb_nodes[0].getClient().get_consensus()
        assert "0x" in consensus['softforks']['light_client']['rfc0043']['threshold']['denom']
        assert "0x" in consensus['softforks']['light_client']['rfc0043']['threshold']['numer']
