import time

from framework.basic_fiber import FiberTest
from framework.test_fiber import FiberConfigPath


class TestP2p(FiberTest):

    def test_old_fiber(self):
        """
        1. start 0.2.0 node
        2. open_channel with node 0.2.0
        3. send_payment with node 0.2.0
        Returns:

        """
        old_fiber = self.start_new_fiber(
            self.generate_account(10000), fiber_version=FiberConfigPath.V020_DEV
        )
        old_fiber.connect_peer(self.fiber1)
        time.sleep(1)
        self.open_channel(
            self.fiber1,
            old_fiber,
            1000 * 100000000,
            1000 * 100000000,
            1000,
            1000,
        )
        self.send_payment(self.fiber1, old_fiber, 100)
        self.send_payment(old_fiber, self.fiber1, 100)
