class TestClass1:
    @classmethod
    def setup_class(cls):
        print("\nSetup TestClass1")

    @classmethod
    def teardown_class(cls):
        print("\nTeardown TestClass1")

    def setup_method(self, method):
        print("\nSetting up method", method.__name__)

    def teardown_method(self, method):
        print("\nTearing down method", method.__name__)

    def test_method1(self):
        print("Executing test_method1")
        x = "this"
        assert "h" in x

    def test_method2(self):
        print("Executing test_method2")
        x = 5
        y = 6
        assert x + 1 == y


class TestClass2:
    @classmethod
    def setup_class(cls):
        print("\nSetup TestClass2")

    @classmethod
    def teardown_class(cls):
        print("\nTeardown TestClass2")

    def setup_method(self, method):
        print("\nSetting up method", method.__name__)

    def teardown_method(self, method):
        print("\nTearing down method", method.__name__)

    def test_method1(self):
        print("Executing test_method1")
        x = "hello"

    def test_method2(self):
        print("Executing test_method2")
        x = 7
        y = 8
        assert x + 1 == y
