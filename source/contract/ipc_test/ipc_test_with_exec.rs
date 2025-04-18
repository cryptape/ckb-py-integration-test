#![no_main]
#![no_std]

ckb_std::entry!(main);
ckb_std::default_alloc!();

fn main() -> i8 {
    ckb_std::syscalls::exec(0, ckb_std::ckb_constants::Source::CellDep, 0, 0, &[]);
    return 0;
}
