#!/bin/bash

# Run pytest and capture the output
pytest_output=$(python3 -m pytest "$1")

# Check if pytest output contains "skipped"
if echo "$pytest_output" | grep -q "skipped"; then
    echo "Test case $1 was skipped"
    exit 0  # Exit with success code
fi

# Check if pytest exited with non-zero status
if [ $? -ne 0 ]; then
    # Handle failed test case
    pkill ckb
    sleep 3
    rm -rf tmp
    echo "Test case $1 failed"
    if [ -e report/report.html ]; then
        mv report/report.html "report/${1////_}_failed.html"
    fi
    exit 1
fi

# Handle successful test case
pkill ckb
sleep 3
rm -rf tmp
rm -rf report/report.html
echo "Test case $1 passed"
exit 0
