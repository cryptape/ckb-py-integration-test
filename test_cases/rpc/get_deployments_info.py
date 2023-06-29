from test_cases.rpc.node_fixture import get_cluster


class TestGetDeploymentsInfo:

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
        invoke rpc get_deployments_info
        - threshold return 0x...
        :return:
        """
        cluster = get_cluster
        deployments_info = cluster.ckb_nodes[0].getClient().get_deployments_info()
        assert "0x" in deployments_info['deployments']['light_client']['threshold']['denom']
        assert "0x" in deployments_info['deployments']['light_client']['threshold']['numer']
