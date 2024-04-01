#!/bin/bash

python3 -m pytest -rs "$1"
pytest_exit_code=$?

if [ "$pytest_exit_code" -ne 0 ]; then
    pkill ckb
    sleep 3
    rm -rf tmp
    echo "run failed "
    if [ -e report/report.html ]; then
        mv report/report.html "report/${1////_}_failed.html"
    fi
    exit "$pytest_exit_code"
fi

pkill ckb
sleep 3
rm -rf tmp
rm -rf report/report.html
echo "run successful"
