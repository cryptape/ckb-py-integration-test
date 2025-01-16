import time

from framework.basic_fiber import FiberTest
from framework.test_fiber import FiberConfigPath


class TestData(FiberTest):

    def test_old_fiber(self):
        """
        1. start fiber 0.2.0
        2. open_channel with fiber
        3. stop fiber
        4. migration and restart fiber 0.3.0
        5. send_payment
        6. shutdown_channel
        Returns:

        """
        # 1. start fiber 0.2.0
        old_fiber_1 = self.start_new_fiber(
            self.generate_account(10000), fiber_version=FiberConfigPath.V020_DEV
        )
        old_fiber_2 = self.start_new_fiber(
            self.generate_account(10000), fiber_version=FiberConfigPath.V020_DEV
        )
        old_fiber_1.connect_peer(old_fiber_2)
        time.sleep(1)
        # 2. open_channel with fiber
        self.open_channel(
            old_fiber_1, old_fiber_2, 1000 * 100000000, 1000 * 100000000, 1000, 1000
        )
        self.send_payment(old_fiber_1, old_fiber_2, 100)

        # 3. stop fiber
        old_fiber_1.stop()
        old_fiber_2.stop()

        #  4. migration and restart fiber 0.3.0
        old_fiber_1.fiber_config_enum = FiberConfigPath.CURRENT_DEV
        old_fiber_2.fiber_config_enum = FiberConfigPath.CURRENT_DEV
        old_fiber_1.migration()
        old_fiber_1.start()
        old_fiber_2.migration()
        old_fiber_2.start()

        # 5. send_payment
        self.send_payment(old_fiber_1, old_fiber_2, 100)
