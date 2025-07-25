import time

from framework.basic_fiber import FiberTest


class MppBench(FiberTest):
    debug = True

    def test_bench_self(self):
        self.fiber3 = self.start_new_fiber(
            self.generate_account(10000, self.fiber1.account_private, 1000 * 100000000)
        )
        self.open_channel(self.fiber1, self.fiber2, 1000 * 100000000, 0, 0, 0)
        self.open_channel(self.fiber1, self.fiber2, 1000 * 100000000, 0, 0, 0)
        self.open_channel(self.fiber2, self.fiber3, 1000 * 100000000, 0, 0, 0)
        self.open_channel(self.fiber2, self.fiber3, 1000 * 100000000, 0, 0, 0)

        self.open_channel(self.fiber3, self.fiber1, 1000 * 100000000, 0, 0, 0)
        self.open_channel(self.fiber3, self.fiber1, 1000 * 100000000, 0, 0, 0)

        time.sleep(10)
        payments = [[]]
        for i in range(100):
            # self.send_invoice_payment(self.fiber1,self.fiber1,2000 * 100000000,False)
            for i in range(3):
                try:
                    payment_hash = self.send_invoice_payment(
                        self.fibers[i], self.fibers[i], 1001 * 100000000, False
                    )
                    payments[i].append(payment_hash)
                except:
                    pass
        for i in range(len(payments)):
            for payment_hash in payments[i]:
                self.wait_payment_finished(self.fibers[i], payment_hash, 1000)
        time.sleep(200)
        self.get_fiber_graph_balance()

    def test_get_fiber_graph_balance(self):
        self.start_new_mock_fiber("")
        self.get_fiber_graph_balance()
