set -e
git clone https://github.com/gpBlockchain/ckb-cli.git
cd ckb-cli
git checkout v114
make prod
cp target/release/ckb-cli ../source/ckb-cli
cd ../
cp download/0.110.2/ckb-cli ./source/ckb-cli-old
git clone https://github.com/nervosnetwork/ckb.git
cd ckb
git checkout pkg/ckb-async-download-rc0
make prod
cd ../
cp -rf download/0.114.0 download/develop
cp ckb/target/prod/ckb download/develop/ckb
#git clone https://github.com/quake/ckb-light-client.git
#cd ckb-light-client
#git checkout quake/fix-set-scripts-partial-bug
#cargo build --release
#cd ../
#mkdir -p download/0.3.5
#cp ckb-light-client/target/release/ckb-light-client download/0.3.5
