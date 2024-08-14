set -e
cp download/0.110.2/ckb-cli ./source/ckb-cli-old
cp download/0.117.0/ckb-cli ./source/ckb-cli
#cp ckb-cli/target/release/ckb-cli download/develop/ckb/target/prod/
#git clone https://github.com/quake/ckb-light-client.git
#cd ckb-light-client
#git checkout quake/fix-set-scripts-partial-bug
#cargo build --release
#cd ../
#mkdir -p download/0.3.5
#cp ckb-light-client/target/release/ckb-light-client download/0.3.5
