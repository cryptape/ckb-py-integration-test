set -e
git clone https://github.com/nervosnetwork/ckb-cli.git
version=`curl -s https://api.github.com/repos/nervosnetwork/ckb-cli/releases/latest | jq -r '.tag_name' `
cd ckb-cli
git checkout $version
make prod
cp target/release/ckb-cli ../source/ckb-cli
cd ../
cp download/0.110.2/ckb-cli ./source/ckb-cli-old
#git clone https://github.com/quake/ckb-light-client.git
#cd ckb-light-client
#git checkout quake/fix-set-scripts-partial-bug
#cargo build --release
#cd ../
#mkdir -p download/0.3.5
#cp ckb-light-client/target/release/ckb-light-client download/0.3.5