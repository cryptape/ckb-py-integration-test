from framework.ckb_light_client_rpc import CKBLightRPCClient
from framework.util import create_config_file, get_project_root, run_command
import shutil
import time
from enum import Enum


class CkbLightClientConfigPath(Enum):
    V0_2_4 = ("source/template/ckb_light_client/0.2.4/testnet.toml.j2", "download/0.2.4/ckb-light-client")

    def __init__(self, ckb_light_client_config_path, ckb_light_bin_path):
        self.ckb_light_client_config_path = ckb_light_client_config_path
        self.ckb_light_bin_path = ckb_light_bin_path

    def __str__(self):
        return self.ckb_light_bin_path.split("/")[-1]


class CkbLightClientNode:

    def __init__(self, ckb_light_client_config_path: CkbLightClientConfigPath, ckb_p2p_infos, ckb_spec_path, rpc_port,
                 tmp_path):
        self.ckbLightClientConfigPath = ckb_light_client_config_path
        self.ckb_p2p_infos = ckb_p2p_infos
        self.ckb_spec_path = ckb_spec_path
        self.rpc_port = rpc_port
        self.tmp_path = f"{get_project_root()}/tmp/{tmp_path}"
        self.ckb_light_config = {
            "ckb_light_client_chain": ckb_spec_path,
            "ckb_light_client_network_bootnodes": ckb_p2p_infos,
            "ckb_light_client_rpc_listen_address": f"127.0.0.1:{rpc_port}"
        }
        self.ckb_light_config_path = f"{self.tmp_path}/testnet.toml"
        self.client = CKBLightRPCClient(f"http://127.0.0.1:{rpc_port}")

    @classmethod
    def init_by_nodes(cls, ckb_light_client_config_path: CkbLightClientConfigPath, ckb_nodes, dec_dir,
                      rpc_port, ):
        ckb_p2p_infos = []
        for node in ckb_nodes:
            address = node.get_peer_address()
            peer_id = node.get_peer_id()
            print(f"{address}/p2p/{peer_id}")
            ckb_p2p_infos.append(f"{address}/p2p/{peer_id}")
        ckb_spec_path = ckb_nodes[0].ckb_specs_config_path
        return CkbLightClientNode(ckb_light_client_config_path, ckb_p2p_infos, ckb_spec_path, rpc_port, dec_dir)

    def prepare(self):
        print("mkdir tmp path ")
        create_config_file(self.ckb_light_config, self.ckbLightClientConfigPath.ckb_light_client_config_path,
                           self.ckb_light_config_path)

        print("init ckb light config ")
        shutil.copy(f"{get_project_root()}/{self.ckbLightClientConfigPath.ckb_light_bin_path}",
                    self.tmp_path)

    def start(self):
        run_command(
            f"cd {self.tmp_path} && RUST_LOG=info,ckb_light_client=trace ./ckb-light-client run --config-file testnet.toml > node.log 2>&1 &")
        # wait rpc start
        time.sleep(2)
        print("start clb_light client ")

    def getClient(self) -> CKBLightRPCClient:
        return self.client

    def stop(self):
        run_command(f"kill $(lsof -t -i:{self.rpc_port})")
        time.sleep(3)

    def clean(self):
        run_command(f"rm -rf {self.tmp_path}")
