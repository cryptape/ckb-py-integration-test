import json

from framework.basic import CkbTest


class TestCkbCommand(CkbTest):

    @classmethod
    def setup_class(cls):
        """
        1. use choose ckb bin
        Returns:

        """
        cls.ckb_version = cls.CkbNodeConfigPath.CURRENT_TEST.value[3]
        print("ckb_version:{0}", cls.ckb_version)
        print(type(cls.ckb_version))

    def test_01_ckb_version(self):
        """
        1.get ckb version use -V
        2.get ckb version use --version
        Returns:

        """
        # 1.get ckb version use -V
        output = self.Ckb_bin.version(self.ckb_version, verbose=False)
        assert (
            "ckb" in output
        ), "The output does not contain the expected substring 'ckb'."
        # 2.get ckb version use --version
        output = self.Ckb_bin.version(self.ckb_version, verbose=True)
        assert (
            "ckb" in output
        ), "The output does not contain the expected substring 'ckb'."
