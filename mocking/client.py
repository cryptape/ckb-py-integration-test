import json
import pathlib
from unittest.mock import Mock
from typing import Optional, Any, List, Union
import abc

class GenericRPCClient(abc.ABC):
    """
    using mocking to test ckb rpc or others
    """
    @abc.abstractmethod
    def call_context(self, result: Union[dict, None], method: str, args: Optional[List[Any]] = None) -> Optional[Exception]:
        pass

    @abc.abstractmethod
    def close(self):
        pass

class JSONError:
    def __init__(self, code: int, message: str, data: Optional[Any] = None):
        self.code = code
        self.message = message
        self.data = data

class JSONRPCMessage:
    def __init__(self, method: str, params_in: Optional[List[Any]] = None):
        self.version = "2.0"
        self.id = str(1)
        self.method = method
        if params_in is not None:
            self.params = json.dumps(params_in)
        else:
            self.params = None
        self.error = None
        self.result = None

class MockClient(GenericRPCClient):
    def __init__(self):
        self.id_counter = 0
        self.mock_json = Mock()

    def new_message(self, method: str, params_in: Optional[List[Any]] = None) -> JSONRPCMessage:
        return JSONRPCMessage(method, params_in)

    def load_mocking_test_from_file(self, t: Any, method: str, params_in: Optional[List[Any]] = None) -> 'MockClient':
        prefix = pathlib.Path("mocking") / method
        response = pathlib.Path(prefix, "response.json").read_text()
        request = pathlib.Path(prefix, "request.json").read_text()
        request_json = self.new_message(method, params_in)
        request_json_msg = json.dumps(request_json.__dict__)
        # Test for request json equivalent
        assert request == request_json_msg, f"failed on json equivalent test: {method}"
        # If last passed, use the generated one(for passing testify validation)
        self.mock_json.configure_mock(**{"mock_json_rpc.return_value": response})
        return self

    def call_context(self, result: Union[dict, None], method: str, args: Optional[List[Any]] = None) -> Optional[Exception]:
        if result is not None:
            raise ValueError(f"call result parameter must be pointer or nil interface: {result}")
        msg = self.new_message(method, args)
        request_json_msg = json.dumps(msg.__dict__)
        # We use str here to avoid json eval on testify
        resp = self.mock_json.mock_json_rpc(request_json_msg)
        rpc_resp = JSONRPCMessage(None)
        rpc_resp.__dict__ = json.loads(resp)
        if rpc_resp.result is not None:
            result = json.loads(rpc_resp.result)
        return None

    def close(self):
        pass

    def load_mocking_test_from_file_patched(self, t: Any, method: str, actual_method: str, args: Optional[List[Any]] = None) -> 'MockClient':
        prefix = pathlib.Path("mocking") / method
        response = pathlib.Path(prefix, "response.json").read_text()
        request = pathlib.Path(prefix, "request.json").read_text()
        request_json = self.new_message(actual_method, args)
        request_json_msg = json.dumps(request_json.__dict__)
        # Test for request json equivalent
        assert request == request_json_msg, f"failed on json equivalent test: {method}"
        # If last passed, use the generated one(for passing testify validation)
        self.mock_json.configure_mock(**{"mock_json_rpc.return_value": response})
        return self
