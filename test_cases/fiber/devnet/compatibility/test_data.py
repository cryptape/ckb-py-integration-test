import time

from framework.basic_fiber import FiberTest
from framework.test_fiber import FiberConfigPath


class TestData(FiberTest):

    def test_old_fiber_020(self):
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
        self.send_payment(old_fiber_2, old_fiber_1, 200)
        channels = old_fiber_1.get_client().list_channels({})
        old_fiber_1.get_client().shutdown_channel(
            {
                "channel_id": channels["channels"][0]["channel_id"],
                "close_script": self.get_account_script(self.Config.ACCOUNT_PRIVATE_1),
                "fee_rate": "0x3FC",
            }
        )
        tx_hash = self.wait_and_check_tx_pool_fee(1000, False, 120)
        tx_message = self.get_tx_message(tx_hash)
        print("tx message:", tx_message)
        assert {
            "args": self.get_account_script(old_fiber_2.account_private)["args"],
            "capacity": 106200000000,
        } in tx_message["output_cells"]

    def test_old_fiber_021(self):
        """
        1. start fiber 0.2.1
        2. open_channel with fiber
        3. stop fiber
        4. migration and restart fiber 0.3.0
        5. send_payment
        6. shutdown_channel
        Returns:

        """
        # 1. start fiber 0.2.0
        old_fiber_1 = self.start_new_fiber(
            self.generate_account(10000), fiber_version=FiberConfigPath.V021_DEV
        )
        old_fiber_2 = self.start_new_fiber(
            self.generate_account(10000), fiber_version=FiberConfigPath.V021_DEV
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
        time.sleep(5)
        old_fiber_1.start()
        time.sleep(5)
        old_fiber_2.migration()
        old_fiber_2.start()

        # 5. send_payment
        self.send_payment(old_fiber_1, old_fiber_2, 100)
        self.send_payment(old_fiber_2, old_fiber_1, 200)
        channels = old_fiber_1.get_client().list_channels({})
        old_fiber_1.get_client().shutdown_channel(
            {
                "channel_id": channels["channels"][0]["channel_id"],
                "close_script": self.get_account_script(self.Config.ACCOUNT_PRIVATE_1),
                "fee_rate": "0x3FC",
            }
        )
        tx_hash = self.wait_and_check_tx_pool_fee(1000, False, 120)
        tx_message = self.get_tx_message(tx_hash)
        print("tx message:", tx_message)
        assert {
            "args": self.get_account_script(old_fiber_2.account_private)["args"],
            "capacity": 106200000000,
        } in tx_message["output_cells"]
