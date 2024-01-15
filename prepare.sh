set -e
git clone https://github.com/gpBlockchain/ckb-cli.git
cd ckb-cli
git checkout exec/data2
make prod
cp target/release/ckb-cli ../source/ckb-cli
cd ../
cp download/0.110.2/ckb-cli ./source/ckb-cli-old
git clone https://github.com/nervosnetwork/ckb-light-client.git
cd ckb-light-client
git checkout develop
cargo build --release
cd ../
mkdir -p download/0.3.5
cp ckb-light-client/target/release/ckb-light-client download/0.3.5