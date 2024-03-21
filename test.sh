python3 -m pytest $1 -x --exitfirst
if [ $? == 1 ];then
    pkill ckb
    sleep 3
    rm -rf tmp
    echo "run failed "
    mv report/report.html report/${1////_}_failed.html
    exit -1
fi
pkill ckb
sleep 3
rm -rf tmp
rm -rf report/report.html
echo "run successful"
