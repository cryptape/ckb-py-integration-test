#!/bin/bash

# Initialize variables to store passed and failed test cases
passed_cases=""
failed_cases="None"

# Function to run pytest and process the output
run_test() {
    # Run pytest with verbose and no capture
    pytest_output=$(python3 -m pytest -v -s "$1")

    # Check if pytest output contains "skipped"
    if echo "$pytest_output" | grep -q "skipped"; then
        echo "Test case $1 was skipped"
        return 0  # Exit with success code
    fi

    # Check if pytest output contains "failed"
    if echo "$pytest_output" | grep -q "failed"; then
        # Handle failed test case
        echo "Test case $1 failed"
        failed_cases+=" $1"
        return 1
    fi

    # Handle successful test case
    echo "Test case $1 passed"
    passed_cases+=" $1"
    return 0
}

# Main loop to run tests for each test case
for test_case in "$@"; do
    run_test "$test_case"
done

# Display summary of test results
echo "Summary:"
echo "Passed test cases:${passed_cases}"
echo "Failed test cases:${failed_cases}"
