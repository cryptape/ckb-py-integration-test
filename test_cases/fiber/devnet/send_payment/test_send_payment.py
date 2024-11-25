from framework.basic_fiber import FiberTest


class TestSendPayment(FiberTest):
    """
    target_pubkey
    amount
    payment_hash
    final_cltv_delta
    invoice
    timeout
    max_fee_amount
    max_parts
    qa
        channel 在各个状态调用 send_payment，只有在ready 才可以
        并发测试
        如何查询过去的交易记录

    """
