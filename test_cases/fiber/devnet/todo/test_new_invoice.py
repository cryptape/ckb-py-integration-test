from framework.basic import CkbTest

# xue


class TestNewInvoice(CkbTest):
    """
    1. 如何查询invoice 状态
    2. 如何取消invoice
    3. 创建invoice 有没有上限
    """

    def test_ckb_amount_is_zero(self):
        """
        amount = 0
        Returns:

        """

    def test_udt_amount_is_0(self):
        """

        Returns:

        """

    def test_ckb_amount_is_1(self):
        """
        ckb amount =1
        Returns:
        """

    def test_udt_amount_is_1(self):
        """
        ckb amount =1
        Returns:
        """

    def test_ckb_amount_gt_channel(self):
        """
        amount > channel
        Returns:

        """

    def test_currency_is_err(self):
        """
        currency !=  当前网络
        Returns:

        """

    def test_description_empty(self):
        """
        description : empty
        Returns:

        """

    def test_description_normal(self):
        """
        description 随机字符串 :sadnand就啊叫啊dd🤔️
        Returns:

        """

    def test_description_very_long(self):
        """
        description length too big
        Returns:

        """

    def test_expiry_zero(self):
        """
        expiry: 0x0
        Returns:

        """

    def test_expiry_not_zero(self):
        """
        expiry: rand data
        Returns:

        """

    def test_payment_preimage_length_too_low(self):
        """
        payment_preimage.length < 32

        Returns:

        """

    def test_payment_preimage_not_exist(self):
        """

        Returns:

        """

    def test_payment_preimage_exist(self):
        """

        Returns:

        """
