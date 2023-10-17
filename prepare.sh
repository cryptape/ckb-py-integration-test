set -e
git clone https://github.com/gpBlockchain/ckb-cli.git
cd ckb-cli
git checkout exec/data2
make prod
cp target/release/ckb-cli ../source/ckb-cli
cd ../
cp download/0.110.2/ckb-cli ./source/ckb-cli-old
#
#cp -r download/0.111.0 download/0.112.0
#git clone https://github.com/nervosnetwork/ckb.git
#cd ckb
#make prod
#cp target/prod/ckb ../download/0.112.0/ckb
#
