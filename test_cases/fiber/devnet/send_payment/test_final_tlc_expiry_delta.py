from framework.basic_fiber import FiberTest


class TestFinalTlcExpiryDelta(FiberTest):

    def test_FinalTlcExpiryDelta(self):
        """
        1. none
        2. 0x0
        3. 0x1
        4. 0xfffffffffffffffffffffffffffffff
        5. 0xfffffffffffffffffffffffffffffffff 溢出
        Returns:

        """
