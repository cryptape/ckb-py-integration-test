set -e
 git clone https://github.com/nervosnetwork/ckb-cli.git
 cd ckb-cli
 git checkout develop
 make prod
 cp target/release/ckb-cli ../source/ckb-cli
 cd ../
 cp download/0.110.2/ckb-cli ./source/ckb-cli-old
 git clone https://github.com/nervosnetwork/fiber
 cd fiber
 cargo build
 cd ../
 mkdir -p download/fiber/0.1.0
 cp fiber/target/debug/fnn download/fiber/0.1.0
#cp download/0.117.0/ckb-cli ./source/ckb-cli
#git clone https://github.com/quake/ckb-light-client.git
#cd ckb-light-client
#git checkout quake/fix-set-scripts-partial-bug
#cargo build --release
#cd ../
#mkdir -p download/0.3.5
#cp ckb-light-client/target/release/ckb-light-client download/0.3.5
