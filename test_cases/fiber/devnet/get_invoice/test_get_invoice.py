import datetime
import time

import pytest

from framework.basic_fiber import FiberTest


class TestGetInvoice(FiberTest):
    """
    1. 能够查询到各种状态的invoice
        cancel_invoice 测试了

    """

    # FiberTest.debug = True

    def test_get_exist_new_invoice(self):
        """
        1. new invoice
            - parse invoice  能够解析 invoice_address ，解析结果和invoice 一致
            -
        Returns:

        """
        invoice = self.fiber1.get_client().new_invoice(
            {
                "amount": hex(1),
                "currency": "Fibd",
                "description": "test invoice generated by node2",
                "expiry": "0xe10",
                "final_cltv": "0x28",
                "payment_preimage": self.generate_random_preimage(),
                "hash_algorithm": "sha256",
            }
        )

        result = self.fiber1.get_client().get_invoice(
            {"payment_hash": invoice["invoice"]["data"]["payment_hash"]}
        )
        node_info = self.fiber1.get_client().node_info()

        assert (
            node_info["public_key"]
            == result["invoice"]["data"]["attrs"][3]["PayeePublicKey"]
        )
        parse_invoice = self.fiber1.get_client().parse_invoice(
            {"invoice": invoice["invoice_address"]}
        )
        assert parse_invoice["invoice"] == invoice["invoice"]
        assert invoice["invoice"]["currency"] == "Fibd"
        assert invoice["invoice"]["amount"] == "0x1"
        assert (
            invoice["invoice"]["data"]["attrs"][0]["Description"]
            == "test invoice generated by node2"
        )
        assert invoice["invoice"]["data"]["attrs"][1]["ExpiryTime"]["secs"] == 3600
        assert invoice["invoice"]["data"]["attrs"][2]["HashAlgorithm"] == "sha256"

        # assert invoice['invoice']['data']['timestamp']
        assert int(int(invoice["invoice"]["data"]["timestamp"], 16) / 1000) == int(
            datetime.datetime.now().timestamp()
        )

    def test_get_not_exist_invoice(self):
        """
        not exist invoice
            return err "invoice not found"
        Returns:

        """

        with pytest.raises(Exception) as exc_info:
            result = self.fiber1.get_client().get_invoice(
                {"payment_hash": self.generate_random_preimage()}
            )
        expected_error_message = "invoice not found"
        assert expected_error_message in exc_info.value.args[0], (
            f"Expected substring '{expected_error_message}' "
            f"not found in actual string '{exc_info.value.args[0]}'"
        )