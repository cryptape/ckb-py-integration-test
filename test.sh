#!/bin/bash

python3 -m pytest "$1" -x --exitfirst
pytest_exit_code=$?

if [ "$pytest_exit_code" -ne 0 ]; then
    pkill ckb
    sleep 3
    rm -rf tmp
    echo "run failed "
    mv report/report.html "report/${1////_}_failed.html"
    exit "$pytest_exit_code"
fi

pkill ckb
sleep 3
rm -rf tmp
rm -rf report/report.html
echo "run successful"
