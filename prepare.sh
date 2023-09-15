set -e
git clone https://github.com/gpBlockchain/ckb-cli.git
cd ckb-cli
git checkout exec/data2
make prod
cp target/release/ckb-cli ../source/ckb-cli
cd ../
cp download/0.110.2/ckb-cli ./source/ckb-cli-old