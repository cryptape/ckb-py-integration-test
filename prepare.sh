set -e
git clone https://github.com/eval-exec/ckb-cli.git
cd ckb-cli
git checkout exec/data2
make prod
cp target/release/ckb-cli ../source/ckb-cli