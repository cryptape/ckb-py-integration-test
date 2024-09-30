from framework.basic import CkbTest
from framework.test_fiber import Fiber, FiberConfigPath


class TestFiber(CkbTest):

    def test_01(self):
        self.Ckb_cli.util_key_info_by_private_key(self.Config.ACCOUNT_PRIVATE_1)
        fiber = Fiber.init_by_port(
            FiberConfigPath.V100,
            self.Config.ACCOUNT_PRIVATE_1,
            "fiber/node",
            "8228",
            "8227",
        )

        fiber.prepare()
        fiber.start()
        print("")
        fiber.get_client().list_channels(
            {"peer_id": "QmdyQWjPtbK4NWWsvy8s69NGJaQULwgeQDT5ZpNDrTNaeV"}
        )
        fiber.stop()
        fiber.clean()
