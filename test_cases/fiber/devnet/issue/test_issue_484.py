import time

import pytest

from framework.basic_fiber import FiberTest


class Test484(FiberTest):
    # FiberTest.debug = True

    # @pytest.mark.skip("https://github.com/nervosnetwork/fiber/pull/484")
    def test_484(self):
        self.open_channel(
            self.fiber1, self.fiber2, 1000 * 100000000, 1000 * 100000000, 1000, 1000
        )
        payment1 = self.send_payment(self.fiber1, self.fiber2, 600 * 100000000, False)
        with pytest.raises(Exception) as exc_info:
            payment2 = self.send_payment(
                self.fiber1, self.fiber2, 600 * 100000000, False, try_count=0
            )
        expected_error_message = "no path found"
        assert expected_error_message in exc_info.value.args[0], (
            f"Expected substring '{expected_error_message}' "
            f"not found in actual string '{exc_info.value.args[0]}'"
        )
        payment3 = self.send_payment(self.fiber1, self.fiber2, 300 * 100000000, False)
        self.wait_payment_state(self.fiber1, payment1, "Success")
        # self.wait_payment_state(self.fiber1, payment2, "Failed")
        self.wait_payment_state(self.fiber1, payment3, "Success")
        self.send_payment(self.fiber2, self.fiber1, 300 * 100000000)
