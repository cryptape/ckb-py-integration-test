import os

import pytest
import json

from mocking.client import MockClient


def load_json_from_file(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data


@pytest.fixture
def mock_client():
    client = MockClient()
    return client


def test_estimate_cycles(mock_client):
    method = 'estimate_cycles'
    script_dir = os.path.dirname(__file__)
    rel_path_request = f"{method}/request.json"
    rel_path_response = f"{method}/response.json"
    request_file = os.path.join(script_dir, rel_path_request)
    response_file = os.path.join(script_dir, rel_path_response)

    # Load the request and response from the files
    request = load_json_from_file(request_file)
    response = load_json_from_file(response_file)

    # Setup the mocking client
    mock_client.load_mocking_test_from_file(None, method, request['params'])

    # Call the method and check the response
    result = {}
    err = mock_client.call_context({}, result, method, request['params'])

    assert err is None

    # Check that the result matches the expected response
    expected_response = response['result']
    assert result == expected_response
