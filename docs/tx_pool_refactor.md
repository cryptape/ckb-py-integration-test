# test_00_rbf_config
## TestRBFConfig
### test_transaction_replacement_disabled_failure

        Disabling RBF (Replace-By-Fee) feature, transaction replacement fails.
        1. starting the node, modify ckb.toml with min_rbf_rate = 800 < min_fee_rate.
            node starts successfully.
        2. send tx use same input cell
            ERROR:  TransactionFailedToResolve: Resolve failed Dead
        :return:
        
### test_disable_rbf_and_check_min_replace_fee

        Disabling RBF (Replace-By-Fee) feature, transaction min_replace_fee is null
         1. starting the node, modify ckb.toml with min_rbf_rate = 800 < min_fee_rate.
            node starts successfully.
        2. send tx and get_transaction
            min_rbf_rate == null
        :return:
        
# test_01_tx_replace_rule
## TestTxReplaceRule
### test_transaction_replacement_with_unconfirmed_inputs_failure

        replace Tx contains unconfirmed inputs, replace failed
        1. a->b ,c->d => a,d -> b
            ERROR :RBF rejected: new Tx contains unconfirmed inputs
        :return:
        
### test_transaction_replacement_with_confirmed_inputs_successful

        replace Tx contains confirmed inputs, replace failed
        1. a->b ,c->d => a,c -> b
            ERROR :RBF rejected: new Tx contains unconfirmed inputs
        :return:
        
### test_transaction_fee_equal_to_old_fee

         replace tx fee  ==  old tx fee

             1. send tx that tx fee == old tx fee
                ERROR : PoolRejectedRBF

             2. get_transaction
                min_fee_rate in PoolRejectedRBF
        :return:
        
### test_transaction_replacement_higher_fee

        Submitting multiple transactions using the same input cell,
            the fee is higher should replace successful
        Steps:
        1. send transaction A, sending input cell to address B
             send successful
        2. send transaction B, sending the same input cell to address B and fee > A(fee)
            send successful
        3. send transaction C, sending the same input cell to address B and fee > B(fee)
            send successful
        4. query transaction (A,B,C) status
              A status : rejected  ; reason : RBFRejected
              B status : rejected  ; reason : RBFRejected
              C status : pending   ;
        :return:
        
### test_transaction_replacement_min_replace_fee

        replace tx use min_replace_fee ,replace successful
        Steps:
        1. send transaction A
             send successful
        2. send transaction B use A.min_replace_fee
            send successful
        4. query transaction (A,B) status
              A status : rejected  ; reason : RBFRejected
              B status : pending   ;
        :return:
        
### test_tx_conflict_too_many_txs

        if the replaced transaction affects more than 100 transactions, the replacement will fail.

            1. send tx A
                send tx successful
            2. send A linked tx 100
                send tx successful
            3. replace A tx
                Error : PoolRejctedRBF
            4. replace first linked tx
                replace successful

            5. query tx pool
                pending tx = 2
        :return:
        
### test_replace_pending_transaction_successful

        replace the pending transaction,replacement successful
            1. send transaction: A
                return tx_hash_a
            2. query transaction tx_hash_a
                A status: pending
            3. replace B=>A
                return tx_hash_b
            4. query transaction tx_hash_a ，query transaction tx_hash_b
                tx_hash_a status: rejected ,reason:RBFRejected
                tx_hash_b status: pending
        :return:
        
### test_replace_proposal_transaction_failure

        Replacing the transaction for the proposal, replacement failed.
        1. Send a transaction and submit it to the proposal.
                Query the transaction status as 'proposal.'
        2. Replace the transaction for that proposal.
            ERROR: RBF rejected: all conflict Txs should be in Pending status
        :return:
        
### test_send_transaction_duplicate_input_with_son_tx

        Replacing the transaction will also remove the child transactions.
        1. send a->b ,b->c, c->d
            successful
        2. Replace a->b, a->d
            successful
        3. query get_tx_pool
            return replace tx: a->d
        4. query old txs status
            status : rejected ,reason:RBFRejected
        :return:
        
### test_

        based on transaction A,
        send a child transaction. The 'min_replace_fee' of transaction A will not change,
        and it can be successfully replaced.

        1. Send transaction A.
            successful
        2. Query the 'min_replace_fee' of transaction A.

        3. Send a child transaction of transaction A.
            successful
        4. Query the updated 'min_replace_fee' of transaction A.
            min_replace_fee unchanged
        5.Send B to replace A.
            replace successful
        :return:
        
### test_min_replace_fee_exceeds_1_ckb

            min_replace_fee exceeds 1 CKB.
            1. send tx(fee=0.9999ckb)
            2. query transaction
                tx.min_replace_fee > 1CKB
        :return:
        
# test_02_txs_lifecycle_chain
## TestTxsLifeCycleChain
### test_high_fee_transaction_priority

         Transactions with higher fees are prioritized to be added to the proposals list,
            but this can result in the parent transaction being stuck in the pending stage.
                When the transaction fee of the child transaction is higher than that of the parent transaction,
                the child transaction will be prioritized and added to the proposals list.

        1. send tx father tx(fee=10000)
        2. send  1500 linked tx(fee=900000)
        3. get_block_template
            proposal length = 1500
            father tx not in proposal list
        :return:
        

**Markers:**
- skip
### test_01

        when a child transaction is confirmed on the chain, if the parent transaction is not in the proposal list,
        the parent transaction will also be added to the transaction list.
        1. send father tx
            successful
        2. send linked tx 10
            successful
        3. remove father tx in the proposals and submit block
            submit  successful
            linked tx stuck in the proposal stage.
            father tx stuck in the pending stage.
        :return:
        

**Markers:**
- skip
# test_03_tx_pool_limit
## TestTxPoolLimit
### test_remove_tx_when_ckb_tx_pool_full

        1. make tx pool full
            tx pool size > ckb_tx_pool_max_tx_pool_size
        2. start miner
            clean tx ,make tx pool size < ckb_tx_pool_max_tx_pool_size
        3. query tx pool size
            tx pool size < ckb_tx_pool_max_tx_pool_size
        :return:
        
### test_max_linked_transactions

        test linked tx limit
        1. keep sending linked transactions until an error occurs
            ERROR :PoolRejectedTransactionByMaxAncestorsCountLimit
        2. query max max_ancestors_count
         max_ancestors_count == 125
        :return:
        
### test_sub_tx

        The sub transactions will not trigger an error until reaching 125
        1. keep sending linked transactions until transaction len > 125
            pass
        :return:
        
# test_04_tx_query
## TestTxQuery
### test_estimate_cycles_pending_tx_successful

        send transaction in pending
            estimate_cycles pending tx will successful
        Steps:
        1. send transaction a-> b
        2. estimate_cycles a->b
        Result:
        1. send successful
        2. estimate_cycles successful
        :return:
        
### test_get_live_cell_pending_tx_input

        send transaction in pending ,
            estimate_cycles pending tx will successful
        Steps:
        1. send transaction a-> b
        2. estimate_cycles a->b
        Result:
        1. send successful
        2. estimate_cycles successful
        :return:
        
### test_get_transaction_contains_fee_and_min_replace_fee_in_pending

        In the pending stages,
            the transaction contains the 'fee' and 'min_replace_fee' fields.
        In the proposal stages,
                the transaction contains the 'fee' ,but not contains 'min_replace_fee' fields.
        In the commit stage, both 'fee' and 'min_replace_fee' will be cleared.


        1. send tx
            successful
        2. get_transaction in pending
            contains fee and min_replace_fee
        3. miner until  get_transaction in proposed
               fee != null,  min_replace_fee == null
        4. miner until get_transaction in committed
                fee == null ,min_replace_fee == null
        
# test_05_node_broadcast
## TestNodeBroadcast
### test_111_p2p_broadcast

        failed replacement transactions from node 111 can be rejected for synchronization by the current node
            1. Send tx-A on node 111.
                send successful
            2. Send tx-B replace tx-A on node 111.
                two tx status: pending
            3. query tx-A,tx-B status on the node 111
                tx-B: pending
                tx-A:pending
            4. query tx-A,tx-B status on the node current
                tx-B: pending
                tx-A:reject
        :return:
        
### test_current_p2p_broadcast

        successful replace transactions from the current node are synchronized to node 111:
            1. send tx-A on the current node.
                Transaction tx-A is sent successfully.
            2. Send tx-B to replace tx-A on the current node.
                The replacement of tx-A with tx-B is successful.
            3. Check the status of tx-A and tx-B on the current node.
                tx-A: rejected
                tx-B: pending
            4. Check the status of tx-A and tx-B on node 111.
                tx-A: pending
                tx-B: pending
            :return:
        
