from framework.basic import CkbTest


###  @xue


class AcceptChannel(CkbTest):
    """
    1. 如何查看未同意的channel
    2. accept_channel，但是余额不足
    3. 同时accept 多个channel
    4. 同意的channel 和 temporary_channel_id 如何关联起来
    """

    def test_temporary_channel_id_not_exist(self):
        """

        Returns:

        """

    def test_ckb_temporary_channel_id_exist(self):
        """
        channel is ckb
        Returns:

        """

    def test_udt_temporary_channel_id_exist(self):
        """
        channel is udt
        Returns:
        """

    def test_funding_amount_zero(self):
        """
        funding_amount :0x0
        Returns:

        """

    def test_ckb_funding_amount_lt_account(self):
        """
        funding_amount < account
        Returns:
        """

    def test_udt_funding_amount_lt_account(self):
        """
        udt < amount
        Returns:

        """

    def test_funding_amount_gt_account(self):
        """
        funding_amount > account
        Returns:

        """

    def test_funding_amount_over_flow(self):
        """
        funding_amount > int.max
        Returns:

        """

    def test_shutdown_script_none(self):
        """
        shutdown_script: none
        Returns:

        """

    def test_shutdown_script(self):
        """

        Returns:

        """

    def test_shutdown_script_too_big(self):
        """
        shutdown_script : data too big ,will cause ckb not enough
        Returns:
        """

    def test_accept_chanel_same_channel_same_time(self):
        """
        accept_chanel 同一时间多次同意同一个channel
        Returns:

        """

    def test_accept_channel_diff_channel_same_time(self):
        """
        accept channel  同一时间多次同意不同的channel
        Returns:

        """
