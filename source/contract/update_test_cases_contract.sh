destination=`pwd`/test_cases
mkdir -p test_cases
git clone https://github.com/gpBlockchain/ckb-test-contracts.git
cd ckb-test-contracts
git checkout fa728703aa5c20376213fb84e381c73e69e20955
cargo install cross --git https://github.com/cross-rs/cross
cargo install ckb-capsule --git https://github.com/quake/capsule.git --branch quake/ckb-0.111
cd rust/acceptance-contracts
capsule build --release
release_dir=target/riscv64imac-unknown-none-elf/release/*
for file in ${release_dir}; do
    echo ${file}
    if [[ -f "$file" && ! "$file" == *.* ]]; then
        cp "$file" "$destination"
    fi
done