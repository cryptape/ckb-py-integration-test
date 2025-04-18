#![no_main]
#![no_std]

use ckb_std::ckb_constants::Source;
use alloc::string::{String, ToString};
use alloc::vec;
use alloc::vec::Vec;
use ckb_std::ckb_types::prelude::Entity;
use ckb_std::high_level::{load_cell, load_cell_capacity, load_cell_data, load_input, load_script, load_script_hash, load_transaction, load_tx_hash};
use ckb_std::syscalls::{current_cycles, exec, load_block_extension, vm_version};
use serde::{Deserialize, Serialize};

ckb_std::entry!(main);
ckb_std::default_alloc!();

#[derive(Serialize, Deserialize, Clone, PartialEq, Debug)]
pub struct BoundaryStruct {
    pub usize_data: usize,
    pub u128_data: u128,
    pub u64_data: u64,
    pub u32_data: u32,
    pub u16_data: u16,
    pub u8_data: u8,
    pub isize_data: isize,
    pub i128_data: i128,
    pub i64_data: i64,
    pub i32_data: i32,
    pub i16_data: i16,
    pub i8_data: i8,
    pub bool_data: bool,
    pub char_data: char,
    pub f32_data: f32,
    pub f64_data: f64,
    pub str_data: String,
}

#[derive(Serialize, Deserialize, Clone, PartialEq, Debug)]
pub struct CkbOpcode {
    pub vm_version: u64,
    load_tx_hash: [u8; 32],
    load_script_hash: [u8; 32],
    load_cell: Vec<u8>,
    load_input: Vec<u8>,
    load_transaction: Vec<u8>,
    load_cell_capacity: u64,
    load_script: Vec<u8>,
    load_cell_data: Vec<u8>,
    load_block_extension: Vec<u8>,
}

impl CkbOpcode {
    fn new() -> Self {
        CkbOpcode {
            vm_version: 0,
            load_tx_hash: [0; 32],
            load_script_hash: [0; 32],
            load_cell: vec![],
            load_input: vec![],
            load_transaction: vec![],
            load_cell_capacity: 0,
            load_script: vec![],
            load_cell_data: vec![],
            load_block_extension: vec![],
        }
    }
}

impl BoundaryStruct {
    fn new() -> Self {
        BoundaryStruct {
            usize_data: 0,
            u128_data: 0,
            u64_data: 0,
            u32_data: 0,
            u16_data: 0,
            u8_data: 0,
            isize_data: 0,
            i128_data: 0,
            i64_data: 0,
            i32_data: 0,
            i16_data: 0,
            i8_data: 0,
            bool_data: false,
            char_data: 'a',
            f32_data: 0.0,
            f64_data: 0.0,
            str_data: "".to_string(),
        }
    }

    pub fn min_value() -> Self {
        BoundaryStruct {
            usize_data: usize::MIN,
            u128_data: u128::MIN,
            u64_data: u64::MIN,
            u32_data: u32::MIN,
            u16_data: u16::MIN,
            u8_data: u8::MIN,
            isize_data: isize::MIN,
            i128_data: i128::MIN,
            i64_data: i64::MIN,
            i32_data: i32::MIN,
            i16_data: i16::MIN,
            i8_data: i8::MIN,
            bool_data: false,
            char_data: ' ',
            f32_data: f32::MIN,
            f64_data: f64::MIN,
            str_data: "".to_string(),
        }
    }

    pub fn max_value() -> Self {
        BoundaryStruct {
            usize_data: usize::MAX,
            u128_data: u128::MAX,
            u64_data: u64::MAX,
            u32_data: u32::MAX,
            u16_data: u16::MAX,
            u8_data: u8::MAX,
            isize_data: 0,
            i128_data: i128::MAX,
            i64_data: i64::MAX,
            i32_data: i32::MAX,
            i16_data: i16::MAX,
            i8_data: i8::MAX,
            bool_data: true,
            char_data: '0',
            f32_data: f32::MAX,
            f64_data: f64::MAX,
            str_data: "max".to_string(),
        }
    }
}


#[ckb_script_ipc::service]
pub trait IpcTest {
    fn math_add(a: u64, b: u64) -> u64;
    fn spawn(s: String) -> String;
    fn syscall_load_script() -> Vec<u8>;
    fn test_boundary_struct(vec: Vec<BoundaryStruct>) -> Vec<BoundaryStruct>;
    fn test_vec(vec: Vec<u8>) -> Vec<u8>;
    fn test_input_vec(vec: Vec<u8>) -> usize;
    fn test_mem(byte_data: usize, kb_data: usize, mb_data: usize) -> Vec<u8>;
    fn test_cycle(cycle_limit: u64) -> usize;
    fn test_input_payload(s: String) -> usize;
    fn test_ckb_call() -> CkbOpcode;
    fn test_empty();
    fn test_current_cycle()->u64; 
}

struct IpcTestServer {}

impl IpcTest for IpcTestServer {
    fn math_add(&mut self, a: u64, b: u64) -> u64 {
        a.checked_add(b).unwrap()
    }

    fn spawn(&mut self, s: String) -> String {
        let argc: u64 = 0;
        let argv = [];
        let mut std_fds: [u64; 2] = [0, 0];
        let mut son_fds: [u64; 3] = [0, 0, 0];
        let (r, w) = ckb_std::syscalls::pipe().unwrap();
        std_fds[0] = r;
        son_fds[1] = w;
        let (r, w) = ckb_std::syscalls::pipe().unwrap();
        std_fds[1] = w;
        son_fds[0] = r;
        let mut pid: u64 = 0;
        let mut spgs = ckb_std::syscalls::SpawnArgs {
            argc,
            argv: argv.as_ptr() as *const *const i8,
            process_id: &mut pid as *mut u64,
            inherited_fds: son_fds.as_ptr(),
        };
        ckb_std::syscalls::spawn(0, ckb_std::ckb_constants::Source::CellDep, 0, 0, &mut spgs)
            .unwrap();
        ckb_std::syscalls::write(std_fds[1], s.as_bytes()).unwrap();
        ckb_std::syscalls::close(std_fds[1]).unwrap();
        let mut buf = [0; 256];
        let buf_len = ckb_std::syscalls::read(std_fds[0], &mut buf).unwrap();
        String::from_utf8_lossy(&buf[..buf_len]).to_string()
    }

    fn syscall_load_script(&mut self) -> Vec<u8> {
        ckb_std::high_level::load_script()
            .unwrap()
            .as_bytes()
            .into()
    }

    fn test_boundary_struct(&mut self, vec: Vec<BoundaryStruct>) -> Vec<BoundaryStruct> {
        if vec.len() == 0 {
            return vec![BoundaryStruct::max_value(), BoundaryStruct::min_value()];
        }
        return vec;
    }
    fn test_vec(&mut self, vec: Vec<u8>) -> Vec<u8> {
        return vec;
    }

    fn test_input_vec(&mut self, vec: Vec<u8>) -> usize {
        return vec.len();
    }

    fn test_cycle(&mut self, cycle_limit: u64) -> usize {
        let mut sum = 0;
        while current_cycles() < cycle_limit {
            sum += 1;
        }
        return current_cycles() as usize;
    }

    fn test_mem(&mut self, byte_data: usize, kb_data: usize, mb_data: usize) -> Vec<u8> {
        let total_bytes = byte_data + (kb_data * 1024) + (mb_data * 1024 * 1024);
        vec![0; total_bytes]
    }

    fn test_input_payload(&mut self, s: String) -> usize {
        return s.len();
    }

    fn test_ckb_call(&mut self) -> CkbOpcode {
        return get_block_opcode();
    }

    fn test_empty(&mut self) -> () {
        // Do nothing
    }

    fn test_current_cycle(&mut self) -> u64 {
        current_cycles()
    }

}

fn get_block_opcode() -> CkbOpcode {
    let mut ckbOpcode = CkbOpcode::new();
    ckbOpcode.vm_version = vm_version().unwrap();
    ckbOpcode.load_tx_hash = load_tx_hash().unwrap();
    ckbOpcode.load_script_hash = load_script_hash().unwrap();
    ckbOpcode.load_cell = load_cell(0, Source::Output).unwrap().as_slice().to_vec();
    ckbOpcode.load_input = load_input(0, Source::Input).unwrap().as_slice().to_vec();
    ckbOpcode.load_transaction = load_transaction().unwrap().as_slice().to_vec();
    ckbOpcode.load_cell_capacity = load_cell_capacity(0, Source::Input).unwrap();
    ckbOpcode.load_script = load_script().unwrap().as_slice().to_vec();
    ckbOpcode.load_cell_data = load_cell_data(0, Source::Input).unwrap();
    let mut data = [0u8; 100];
    let result = load_block_extension(&mut data, 0, 0, Source::CellDep).unwrap();
    ckbOpcode.load_block_extension = data.to_vec();

    return ckbOpcode;
}


fn main() -> i8 {
    ckb_script_ipc_common::spawn::run_server(IpcTestServer {}.server()).unwrap();
    return 0;
}


