import time
from abc import ABC, abstractmethod
from enum import Enum
from framework.util import create_config_file, get_project_root, run_command, get_ckb_configs
from framework.config import get_tmp_path, CKB_DEFAULT_CONFIG, CKB_MINER_CONFIG
from framework.rpc import RPCClient
import shutil


class CkbNodeConfigPath(Enum):
    CURRENT_TEST = ("template/ckb/v110/ckb.toml.j2",
                    "template/ckb/v110/ckb-miner.toml.j2",
                    "template/ckb/v110/specs/dev.toml",
                    "download/0.110.0")
    V110 = ("", "", "", "")
    V109 = ("", "", "", "")
    v108 = ("", "", "", "")

    def __init__(self, ckb_config_path, ckb_miner_config_path, ckb_spec_path, ckb_bin_path):
        self.ckb_config_path = ckb_config_path
        self.ckb_miner_config_path = ckb_miner_config_path
        self.ckb_spec_path = ckb_spec_path
        self.ckb_bin_path = ckb_bin_path


class LightCkbNodeConfigPath(Enum):
    V1 = ('todo')

    def __init__(self, ckb_light_ckb_config_path):
        self.ckb_light_ckb_config_path = ckb_light_ckb_config_path


class Node(ABC):

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def prepare(self):
        pass

    @abstractmethod
    def clean(self):
        pass

    @abstractmethod
    def miner(self, number):
        pass

    @abstractmethod
    def version(self):
        pass

    @abstractmethod
    def restart(self, config):
        pass

    @abstractmethod
    def getClient(self):
        pass


class CkbNode(Node):

    @classmethod
    def init_dev_by_port(cls, ckb_node_path_enum: CkbNodeConfigPath, dec_dir, rpc_port, p2p_port):
        ckb_config, ckb_miner_config, ckb_specs_config = get_ckb_configs(p2p_port, rpc_port)
        return CkbNode(ckb_node_path_enum, dec_dir, ckb_config, ckb_miner_config, ckb_specs_config)

    def __init__(self, ckb_node_path_enum: CkbNodeConfigPath,
                 dec_dir,
                 ckb_config=CKB_DEFAULT_CONFIG,
                 ckb_miner_config=CKB_MINER_CONFIG,
                 ckb_specs_config={},
                 ):
        self.ckb_config_path = ckb_node_path_enum
        self.dec_path = ckb_config
        self.ckb_config = ckb_config.copy()
        self.ckb_miner_config = ckb_miner_config
        self.ckb_specs_config = ckb_specs_config
        self.ckb_dir = "{tmp}/{ckb_dir}".format(tmp=get_tmp_path(), ckb_dir=dec_dir)
        self.ckb_bin_path = "{ckb_dir}/ckb".format(ckb_dir=self.ckb_dir)
        self.ckb_toml_path = "{ckb_dir}/ckb.toml".format(ckb_dir=self.ckb_dir)
        self.ckb_miner_toml_path = "{ckb_dir}/ckb-miner.toml".format(ckb_dir=self.ckb_dir)
        self.ckb_pid = -1
        self.ckb_miner_pid = -1
        self.rpcUrl = "http://{url}".format(url=self.ckb_config.get("ckb_rpc_listen_address", "127.0.0.1:8114"))
        self.client = RPCClient(self.rpcUrl)

    def get_peer_id(self):
        return self.client.local_node_info()["node_id"]

    def get_peer_address(self):
        info = self.client.local_node_info()
        return info["addresses"][0]['address'].replace("0.0.0.0", "127.0.0.1")

    def get_connected_count(self):
        return int(self.getClient().local_node_info()["connections"], 16)

    def connected(self, node):
        peer_id = node.get_peer_id()
        peer_address = node.get_peer_address()
        print("add node response:", self.getClient().add_node(peer_id, peer_address))

    def getClient(self):
        return self.client

    def restart(self, config):
        pass

    def start(self):
        self.ckb_pid = run_command("cd {ckb_dir} && ./ckb run --indexer > node.log 2>&1 &".format(ckb_dir=self.ckb_dir))
        # //todo replace by rpc
        time.sleep(3)

    def stop(self):
        run_command("kill {pid}".format(pid=self.ckb_pid))
        self.ckb_pid = -1

    def prepare(self):
        create_config_file(self.ckb_config, self.ckb_config_path.ckb_config_path,
                           self.ckb_toml_path)
        create_config_file(self.ckb_miner_config, self.ckb_config_path.ckb_miner_config_path, self.ckb_miner_toml_path)
        shutil.copy("{root_path}/{ckb_bin_path}/ckb".format(root_path=get_project_root(),
                                                            ckb_bin_path=self.ckb_config_path.ckb_bin_path),
                    self.ckb_dir)

        shutil.copy("{root_path}/{ckb_bin_path}/ckb-cli".format(root_path=get_project_root(),
                                                                ckb_bin_path=self.ckb_config_path.ckb_bin_path),
                    self.ckb_dir)

        shutil.copy("{root_path}/template/ckb/default.db-options".format(root_path=get_project_root()), self.ckb_dir)
        shutil.copy("{root_path}/{spec_path}".format(root_path=get_project_root(),
                                                     spec_path=self.ckb_config_path.ckb_spec_path), self.ckb_dir)

        # create_config_file(self.ckb_miner_config, self.ckb_config_path.ckb_miner_config_path, dec_dir)
        # create_config_file(self.ckb_specs_config, self.ckb_config_path.ckb_miner_config_path, dec_dir)
        #     if self.ckb_config_path.ckb_spec_path == "dev":
        #         pass

    def clean(self):
        run_command("rm -rf {ckb_dir}".format(ckb_dir=self.ckb_dir))

    def miner(self, number):
        pass

    def start_miner(self):
        self.ckb_miner_pid = run_command(
            "cd {ckb_dir} && ./ckb miner > ckb.miner.log 2>&1  &".format(ckb_dir=self.ckb_dir))
        # replace check height upper
        time.sleep(3)

    def stop_miner(self):
        run_command("kill {pid}".format(pid=self.ckb_miner_pid))
        self.ckb_miner_pid = -1

    def version(self):
        pass


class CkbLightClient(Node):

    def restart(self, config):
        pass

    def __init__(self):
        pass

    def start(self):
        pass

    def stop(self):
        pass

    def prepare(self):
        pass

    def clean(self):
        pass

    def miner(self, number):
        pass

    def version(self):
        pass

    def getClient(self):
        pass