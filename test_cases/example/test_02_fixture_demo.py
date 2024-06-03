import pytest


@pytest.fixture(scope="module")
def setup_and_teardown():
    print("\nSetup")
    setup_data = {"key": "value"}
    yield setup_data
    print("\nTeardown")


class TestClass1:
    def test_method1(self, setup_and_teardown):
        print("Executing test_method1")
        print("Setup data is: ", setup_and_teardown)
        x = "this"
        assert "h" in x

    def test_method2(self, setup_and_teardown):
        print("Executing test_method2")
        print("Setup data is: ", setup_and_teardown)
        x = 5
        y = 6
        assert x + 1 == y


class TestClass2:
    def test_method1(self, setup_and_teardown):
        print("Executing test_method1")
        print("Setup data is: ", setup_and_teardown)

    def test_method2(self, setup_and_teardown):
        print("Executing test_method2")
        print("Setup data is: ", setup_and_teardown)
        x = 7
        y = 8
        assert x + 1 == y
