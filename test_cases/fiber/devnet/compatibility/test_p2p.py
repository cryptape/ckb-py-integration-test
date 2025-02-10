import time

import pytest

from framework.basic_fiber import FiberTest
from framework.test_fiber import FiberConfigPath


class TestP2p(FiberTest):

    @pytest.mark.skip("not support old fiber")
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
        old_fiber.get_client().open_channel(
            {
                "peer_id": self.fiber1.get_peer_id(),
                "funding_amount": hex(1000 + 62 * 100000000),
                "tlc_fee_proportional_millionths": hex(1000),
                "public": True,
            }
        )

        old_fiber.get_client().open_channel(
            {
                "peer_id": self.fiber1.get_peer_id(),
                "funding_amount": hex(2000 * 100000000),
                "tlc_fee_proportional_millionths": hex(1000),
                "public": True,
            }
        )
        self.fiber1.get_client().open_channel(
            {
                "peer_id": old_fiber.get_peer_id(),
                "funding_amount": hex(2000 * 100000000),
                "tlc_fee_proportional_millionths": hex(1000),
                "public": True,
            }
        )
        self.open_channel(
            self.fiber1, self.fiber2, 1000 * 100000000, 1000 * 100000000, 1000, 1000
        )
        with pytest.raises(Exception) as exc_info:
            self.send_payment(old_fiber, self.fiber1, 100)
        expected_error_message = "no path found"
        assert expected_error_message in exc_info.value.args[0], (
            f"Expected substring '{expected_error_message}' "
            f"not found in actual string '{exc_info.value.args[0]}'"
        )
