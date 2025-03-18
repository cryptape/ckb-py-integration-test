# RBF (Replace-By-Fee) Tests Mind Map

```mermaid
flowchart TD
  %% 主节点样式
  classDef rootNode fill:#4169E1,stroke:#000,stroke-width:2px,color:white,font-weight:bold,font-size:16px
  %% 一级节点样式
  classDef level1Node fill:#FFFFCC,stroke:#000,stroke-width:1px
  %% 二级节点样式
  classDef level2Node fill:#CCFFCC,stroke:#000,stroke-width:1px
  %% 测试用例节点样式
  classDef testNode fill:#FFFFCC,stroke:#000,stroke-width:1px
  
  %% 主节点
  RBFTests(("RBF Tests"))
  class RBFTests rootNode
  
  %% 一级节点
  test_00_rbf_config["test_00_rbf_config"]
  test_01_tx_replace_rule["test_01_tx_replace_rule"]
  
  %% 二级节点
  TestRBFConfig["TestRBFConfig"]
  TestTxReplaceRule["TestTxReplaceRule"]
  
  %% 测试用例节点
  test_transaction_replacement_disabled_failure["test_transaction_replacement_disabled_failure<br>- Disable RBF with min_rbf_rate < min_fee_rate<br>- Send tx with same input cell<br>- ERROR: TransactionFailedToResolve: Resolve failed Dead"]
  
  test_disable_rbf_and_check_min_replace_fee["test_disable_rbf_and_check_min_replace_fee<br>- Disable RBF with min_rbf_rate < min_fee_rate<br>- Send tx and get_transaction<br>- Verify min_rbf_rate == null"]
  
  test_transaction_replacement_with_unconfirmed_inputs_failure["test_transaction_replacement_with_unconfirmed_inputs_failure<br>- a->b, c->d => a,d -> b<br>- ERROR: RBF rejected: new Tx contains unconfirmed inputs"]
  
  test_transaction_replacement_with_confirmed_inputs_successful["test_transaction_replacement_with_confirmed_inputs_successful<br>- a->b, c->d => a,c -> b<br>- ERROR: RBF rejected: new Tx contains unconfirmed inputs"]
  
  test_transaction_fee_equal_to_old_fee["test_transaction_fee_equal_to_old_fee<br>- Send tx with fee == old tx fee<br>- ERROR: PoolRejectedRBF<br>- Verify min_fee_rate in PoolRejectedRBF"]
  
  test_transaction_replacement_higher_fee["test_transaction_replacement_higher_fee<br>- Send tx A with input cell to address B<br>- Send tx B with same input cell and fee > A(fee)<br>- Send tx C with same input cell and fee > B(fee)<br>- Verify A,B rejected with RBFRejected, C pending"]
  
  test_transaction_replacement_min_replace_fee["test_transaction_replacement_min_replace_fee<br>- Send tx A successfully<br>- Send tx B using A.min_replace_fee<br>- Verify A rejected with RBFRejected, B pending"]
  
  test_tx_conflict_too_many_txs["test_tx_conflict_too_many_txs<br>- Send tx A successfully<br>- Send 100 linked txs to A<br>- Replace A tx (fails with PoolRejctedRBF)<br>- Replace first linked tx (succeeds)<br>- Verify pending tx count = 2"]
  
  test_replace_pending_transaction_successful["test_replace_pending_transaction_successful<br>- Send tx A (pending)<br>- Replace with tx B<br>- Verify A rejected with RBFRejected, B pending"]
  
  test_replace_proposal_transaction_failure["test_replace_proposal_transaction_failure<br>- Send tx and submit to proposal<br>- Try to replace proposal tx<br>- ERROR: RBF rejected: all conflict Txs should be in Pending status"]
  
  test_send_transaction_duplicate_input_with_son_tx["test_send_transaction_duplicate_input_with_son_tx<br>- Send a->b, b->c, c->d<br>- Replace a->b with a->d<br>- Verify tx pool has a->d<br>- Verify old txs rejected with RBFRejected"]
  
  test_min_replace_fee_unchanged_with_child_tx["test_min_replace_fee_unchanged_with_child_tx<br>- Send tx A<br>- Check min_replace_fee<br>- Send child tx of A<br>- Verify min_replace_fee unchanged<br>- Replace A with B successfully"]
  
  test_min_replace_fee_exceeds_1_ckb["test_min_replace_fee_exceeds_1_ckb<br>- Send tx with fee=0.9999ckb<br>- Verify tx.min_replace_fee > 1CKB"]
  
  %% 连接关系
  RBFTests --> test_00_rbf_config
  RBFTests --> test_01_tx_replace_rule
  
  test_00_rbf_config --> TestRBFConfig
  test_01_tx_replace_rule --> TestTxReplaceRule
  
  TestRBFConfig --> test_transaction_replacement_disabled_failure
  TestRBFConfig --> test_disable_rbf_and_check_min_replace_fee
  
  TestTxReplaceRule --> test_transaction_replacement_with_unconfirmed_inputs_failure
  TestTxReplaceRule --> test_transaction_replacement_with_confirmed_inputs_successful
  TestTxReplaceRule --> test_transaction_fee_equal_to_old_fee
  TestTxReplaceRule --> test_transaction_replacement_higher_fee
  TestTxReplaceRule --> test_transaction_replacement_min_replace_fee
  TestTxReplaceRule --> test_tx_conflict_too_many_txs
  TestTxReplaceRule --> test_replace_pending_transaction_successful
  TestTxReplaceRule --> test_replace_proposal_transaction_failure
  TestTxReplaceRule --> test_send_transaction_duplicate_input_with_son_tx
  TestTxReplaceRule --> test_min_replace_fee_unchanged_with_child_tx
  TestTxReplaceRule --> test_min_replace_fee_exceeds_1_ckb
  
  %% 应用样式
  class test_00_rbf_config,test_01_tx_replace_rule level1Node
  class TestRBFConfig,TestTxReplaceRule level2Node
  class test_transaction_replacement_disabled_failure,test_disable_rbf_and_check_min_replace_fee,test_transaction_replacement_with_unconfirmed_inputs_failure,test_transaction_replacement_with_confirmed_inputs_successful,test_transaction_fee_equal_to_old_fee,test_transaction_replacement_higher_fee,test_transaction_replacement_min_replace_fee,test_tx_conflict_too_many_txs,test_replace_pending_transaction_successful,test_replace_proposal_transaction_failure,test_send_transaction_duplicate_input_with_son_tx,test_min_replace_fee_unchanged_with_child_tx,test_min_replace_fee_exceeds_1_ckb testNode
```