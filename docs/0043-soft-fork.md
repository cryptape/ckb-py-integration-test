# test_devnet_soft_fork
## TestDevNetSoftFork
### test_01_get_consensus

        rfc0043 min_activation_epoch  is 0x0
        1. query  get_consensus
        return consensus['softforks']['light_client']['rfc0043']['min_activation_epoch'] == "0x0"
        :return:
        
### test_02_get_deployments_info

        rfc0043 is active in block :0
        1. query tip number
            return 0
        2. query get_deployments_info
            info['deployments']['light_client']['state'] == 'active'
        :return:
        
### test_03_get_block_tmp

        block template contains extension
        1. query get_block_template
            template['extension'] is not None
        :return:
        
# test_mainnet_soft_fork_failed
## TestMainNetSoftForkFailed
### test_get_consensus_in_ge_110

        > 110 node softforks:light_client min_activation_epoch ==  0x21c8
        > 110 node softforks:light_client start == 0x205a
        > 110 node softforks:light_client timeout == 0x2168
        1. query get_consensus
        :return:
        
### test_get_consensus_in_lt_110

        < 110 node  softforks == {}
        :return:
        
### test_get_deployments_in_gt_110

        > 110 node deployments:light_client min_activation_epoch ==  0x21c8
        > 110 node deployments:light_client period == 0x2a
        > 110 node deployments:light_client timeout == 0x2168
        1. query get_deployments_info
        :return:
        
### test_miner_use_109

        use 109 miner block,will cause softfork failed
        1. 109 node miner to 8314
            query 110 node statue == defined
        2. 109 node miner to 8915
            query 110 node statue == started
        3. 109 node miner to 8566
            query 110 node statue == started
        4. 109 node miner to 8567
            query 110 node statue == failed
        :return:
        
# test_mainnet_soft_fork_successful
## TestMainNetSoftForkSuccessful
### test_miner_use_110

        110 node miner will cause softfork active
        1. 110 node miner to 8314
            node.state == defined
        2. 110 node miner to 8315
            node.state == started
        3. 110 node miner to 8356
            node.state == started
        4. 110 node miner to 8567
            node.state == locked_in
        5. 110 node miner to 8650
            node.state == locked_in
        6. 110 node miner to 8651
            node.state == active
        :return:
        
# test_mainnet_soft_fork_with_ckb_light_client
## TestMainnetSoftForkWithCkbLightClient
### test_soft_fork_activation_light_node

        Soft fork transitioning from 'defined' to 'active' will not
        affect the synchronization of light nodes.
        1. Mine until block 10000.
            Successful.
        2. Wait for light nodes to synchronize up to block 10000.
            Successful.
        3. Query the balance of the mining address.
            Light node == node.
        :return:
        
