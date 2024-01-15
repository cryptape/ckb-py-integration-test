git clone https://github.com/nervosnetwork/ckb-light-client.git
cd ckb-light-client
git checkout develop
cargo build --release
cd ../
mkdir -p download/0.3.5
cp ckb-light-client/target/release/ckb-light-client download/0.3.5