import time

from framework.basic_fiber import FiberTest


class MutilPathTestCase(FiberTest):
    # debug = True

    def test_mutil_to_one(self):
        """

        - a-1-b-1-c
        - a-2-b-1-c
        - a-1-d-1-b-1-c
        - a-2-d-1-b-1-c
        Returns:
        """
        self.start_new_fiber(
            self.generate_account(10000, self.fiber1.account_private, 1000 * 100000000)
        )
        self.start_new_fiber(
            self.generate_account(10000, self.fiber1.account_private, 1000 * 100000000)
        )

        self.open_channel(
            self.fibers[0], self.fibers[1], 1000 * 100000000, 1000 * 100000000,0,0
        )
        self.open_channel(
            self.fibers[0], self.fibers[1], 1000 * 100000000, 1000 * 100000000,0,0
        )

        self.open_channel(
            self.fibers[0], self.fibers[3], 1000 * 100000000, 1000 * 100000000,0,0
        )
        self.open_channel(
            self.fibers[0], self.fibers[3], 1000 * 100000000, 1000 * 100000000,0,0
        )

        self.open_channel(
            self.fibers[3], self.fibers[2], 2000 * 100000000, 1000 * 100000000,0,0
        )
        self.open_channel(
            self.fibers[1], self.fibers[2], 2000 * 100000000, 1000 * 100000000,0,0
        )

        self.send_invoice_payment(self.fibers[0], self.fibers[2], 4000 * 100000000)

    def test_mutil_to_one_2(self):
        self.start_new_fiber(
            self.generate_account(10000, self.fiber1.account_private, 1000 * 100000000)
        )
        self.start_new_fiber(
            self.generate_account(10000, self.fiber1.account_private, 1000 * 100000000)
        )

        self.open_channel(self.fibers[0], self.fibers[1], 1000 * 100000000, 0, 0, 0)
        self.open_channel(self.fibers[0], self.fibers[1], 1000 * 100000000, 0, 0, 0)

        self.open_channel(self.fibers[0], self.fibers[3], 1000 * 100000000, 0, 0, 0)
        self.open_channel(self.fibers[0], self.fibers[3], 1000 * 100000000, 0, 0, 0)

        self.open_channel(self.fibers[3], self.fibers[2], 2000 * 100000000, 0, 0, 0)
        self.open_channel(self.fibers[1], self.fibers[2], 2000 * 100000000, 0, 0, 0)

        time.sleep(10)
        self.send_invoice_payment(self.fibers[0], self.fibers[2], 2000 * 100000000)
        self.send_invoice_payment(self.fibers[0], self.fibers[2], 2000 * 100000000)
        time.sleep(10)
        try:
            self.send_invoice_payment(self.fibers[0], self.fibers[2], 2000 * 100000000)
        except Exception as e:
            pass
        self.send_invoice_payment(self.fibers[2], self.fibers[0], 2000 * 100000000)
        self.send_invoice_payment(self.fibers[2], self.fibers[0], 2000 * 100000000)
        print("self.send_payment(self.fibers[0],self.fibers[2], 1 * 100000000)")
        self.send_invoice_payment(self.fibers[0], self.fibers[2], 1 * 100000000)


    def test_mutil_to_one_3(self):
        self.start_new_fiber(
            self.generate_account(10000, self.fiber1.account_private, 1000 * 100000000)
        )
        self.start_new_fiber(
            self.generate_account(10000, self.fiber1.account_private, 1000 * 100000000)
        )

        self.open_channel(
            self.fibers[0], self.fibers[1], 1000 * 100000000, 0, 1000, 1000
        )
        self.open_channel(
            self.fibers[0], self.fibers[1], 1000 * 100000000, 0, 1000, 1000
        )

        self.open_channel(
            self.fibers[0], self.fibers[3], 1000 * 100000000, 0, 1000, 1000
        )
        self.open_channel(
            self.fibers[0], self.fibers[3], 1000 * 100000000, 0, 1000, 1000
        )

        self.open_channel(
            self.fibers[3], self.fibers[2], 2000 * 100000000, 0, 1000, 1000
        )
        self.open_channel(
            self.fibers[1], self.fibers[2], 2000 * 100000000, 0, 1000, 1000
        )
        self.wait_graph_channels_sync(self.fiber1, 6)
        self.wait_graph_channels_sync(self.fiber2, 6)
        self.wait_graph_channels_sync(self.fibers[2], 6)
        self.wait_graph_channels_sync(self.fibers[3], 6)

        # print("channels len:", len(channels["channels"]))
        # for i in range(3):
        #     self.send_invoice_payment(self.fibers[0], self.fibers[2], 1000 * 100000000)

        # for i in range(10):
        #     self.send_invoice_payment(self.fibers[0], self.fibers[2], 4000 * 100000000)
        #     self.send_invoice_payment(self.fibers[2], self.fibers[0], 4000 * 100000000)

    def test_0012(self):
        # for i in range(10):
        self.start_new_mock_fiber("")
        self.start_new_mock_fiber("")
        # for i in range(3):
        self.send_invoice_payment(self.fibers[0], self.fibers[2], 3000 * 100000000)

        # self.fibers[0].stop()
        # self.fibers[0].start()
        # time.sleep(10)
        # self.send_invoice_payment(self.fibers[0], self.fibers[2], 2000 * 100000000)

    def test_0013(self):
        self.fiber1.stop()
        self.fiber1.start()

    def test_one_to_mutil(self):
        """
        - a-1-b-1-c
        - a-1-b-2-c
        - a-1-b-1-d-1-c
        Returns:

        """
        self.start_new_fiber(
            self.generate_account(10000, self.fiber1.account_private, 1000 * 100000000)
        )
        self.start_new_fiber(
            self.generate_account(10000, self.fiber1.account_private, 1000 * 100000000)
        )

        self.open_channel(
            self.fibers[0], self.fibers[1], 1000 * 100000000, 1000 * 100000000
        )
        self.open_channel(
            self.fibers[0], self.fibers[3], 1000 * 100000000, 1000 * 100000000
        )

        self.open_channel(
            self.fibers[3], self.fibers[2], 2000 * 100000000, 1000 * 100000000
        )
        self.open_channel(
            self.fibers[1], self.fibers[2], 2000 * 100000000, 1000 * 100000000
        )
        time.sleep(10)
        self.send_invoice_payment(self.fibers[0], self.fibers[2], 3000 * 100000000)

    def test_one_to_mutil_2(self):
        self.start_new_mock_fiber("")
        self.start_new_mock_fiber("")
        self.send_invoice_payment(self.fibers[0], self.fibers[3], 1000 * 100000000)

    def test_00021(self):
        self.start_new_mock_fiber("")
        self.start_new_mock_fiber("")
        # self.fibers[0].stop()
        # self.fibers[0].start()
        # time.sleep(10)
        # self.send_invoice_payment(self.fibers[0], self.fibers[2], 1000 * 100000000)
        self.send_invoice_payment(self.fibers[0], self.fibers[2], 2000 * 100000000)
        self.send_invoice_payment(self.fibers[0], self.fibers[2], 2000 * 100000000)
        try:
            self.send_invoice_payment(self.fiber1, self.fibers[2], 2000 * 100000000)
        except Exception as e:
            pass
        self.send_invoice_payment(self.fibers[2], self.fiber1, 2000 * 100000000)
        self.send_invoice_payment(self.fibers[2], self.fiber1, 2000 * 100000000)
        print("self.send_payment(self.fiber1,self.fibers[2], 1 * 100000000)")
        self.send_invoice_payment(self.fiber1, self.fibers[2], 1 * 100000000)

    def test_001(self):
        self.start_new_mock_fiber("")
        self.start_new_mock_fiber("")
        self.get_fiber_graph_balance()
        # self.send_invoice_payment(self.fibers[2], self.fibers[0], 2000 * 100000000)

        # print(msg)
        # self.get_fibers_balance_message()

    def test_graph(self):
        pass
