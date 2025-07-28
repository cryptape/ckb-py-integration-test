import time

from framework.basic_fiber import FiberTest
from framework.test_fiber import FiberConfigPath


class TestMppDemo(FiberTest):

    def test_mpp_demo(self):
        """
        open channel with mpp

        Returns:

        """
        self.open_channel(self.fiber1, self.fiber2, 1000 * 100000000, 0)
        self.open_channel(self.fiber1, self.fiber2, 1000 * 100000000, 0)
        self.open_channel(self.fiber1, self.fiber2, 1000 * 100000000, 0)
        # time.sleep(10)
        for i in range(10):
            print(f"-----current--{i}")
            self.send_invoice_payment(self.fiber1, self.fiber2, 2100 * 100000000)
            time.sleep(10)
            self.send_invoice_payment(self.fiber2, self.fiber1, 2100 * 100000000)
            time.sleep(10)
        msg = self.get_fibers_balance_message()
        print(msg)
