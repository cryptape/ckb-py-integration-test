#!/bin/bash

# Initialize variables to store passed and failed test cases
passed_cases=""
failed_cases=""

# Function to run pytest and process the output
run_test() {
    # Run pytest and capture the output
    pytest_output=$(python3 -m pytest "$1")

    # Check if pytest output contains "skipped"
    if echo "$pytest_output" | grep -q "skipped"; then
        echo "Test case $1 was skipped"
        return 0  # Exit with success code
    fi

    # Check if pytest exited with non-zero status
    if [ $? -ne 0 ]; then
        # Handle failed test case
        echo "Test case $1 failed"
        failed_cases+=" $1"
        pkill ckb
        sleep 3
        rm -rf tmp
        if [ -e report/report.html ]; then
            mv report/report.html "report/${1////_}_failed.html"
        fi
        return 1
    fi

    # Handle successful test case
    echo "Test case $1 passed"
    passed_cases+=" $1"
    pkill ckb
    sleep 3
    rm -rf tmp
    rm -rf report/report.html
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
