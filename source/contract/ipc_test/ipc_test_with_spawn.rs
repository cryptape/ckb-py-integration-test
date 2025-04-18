#![no_main]
#![no_std]

ckb_std::entry!(main);
ckb_std::default_alloc!();

fn main() -> i8 {
    let mut std_fds: [u64; 2] = [0; 2];
    ckb_std::syscalls::inherited_fds(&mut std_fds);
    let mut buf = [0; 256];
    let buf_len = ckb_std::syscalls::read(std_fds[0], &mut buf).unwrap();
    ckb_std::syscalls::write(std_fds[1], &buf[..buf_len]).unwrap();
    ckb_std::syscalls::close(std_fds[1]).unwrap();
    return 0;
}
