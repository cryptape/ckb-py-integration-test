import shutil
from enum import Enum
import time
from framework.util import (
    create_config_file,
    get_project_root,
    run_command,
)
from framework.fiber_rpc import FiberRPCClient
from framework.config import get_tmp_path


class FiberConfigPath(Enum):
    V100 = ("/source/template/fiber/config.yml.j2", "download/fiber/0.1.0/fnn")

    def __init__(self, fiber_config_path, fiber_bin_path):
        self.fiber_config_path = fiber_config_path
        self.fiber_bin_path = fiber_bin_path

    def __str__(self):
        return self.fiber_bin_path.split("/")[-2]


class Fiber:

    @classmethod
    def init_by_port(
        cls,
        fiber_config_path: FiberConfigPath,
        account_private,
        tmp_path,
        rpc_port,
        p2p_port,
    ):
        config = {
            "fiber_listening_addr": f"/ip4/127.0.0.1/tcp/{p2p_port}",
            "rpc_listening_addr": f"127.0.0.1:{rpc_port}",
        }
        return Fiber(fiber_config_path, account_private, tmp_path, config)

    @classmethod
    def init_with_sk(cls):
        pass

    def __init__(
        self,
        fiber_config_path: FiberConfigPath,
        account_private,
        tmp_path,
        sk=None,
        config=None,
    ):
        if config is None:
            config = {
                "fiber_listening_addr": "/ip4/127.0.0.1/tcp/8228",
                "rpc_listening_addr": "127.0.0.1:8227",
            }
        self.fiber_config_enum = fiber_config_path
        self.fiber_config = {
            "fiber_listening_addr": config["fiber_listening_addr"],
            "rpc_listening_addr": config["rpc_listening_addr"],
        }
        self.account_private = account_private
        self.tmp_path = f"{get_tmp_path()}/{tmp_path}"
        self.fiber_config_path = f"{self.tmp_path}/config.yml"
        self.client = FiberRPCClient(f"http://{config['rpc_listening_addr']}")
        self.rpc_port = config["rpc_listening_addr"].split(":")[-1]
        self.sk = sk

    def prepare(self, update_config=None):
        if update_config is None:
            update_config = {}
        self.fiber_config.update(update_config)
        # check file exist
        create_config_file(
            self.fiber_config,
            self.fiber_config_enum.fiber_config_path,
            self.fiber_config_path,
        )
        with open(f"{self.tmp_path}/ckb/key", "w") as f:
            f.write(self.account_private.replace("0x", ""))
        # node
        if self.sk is None:
            return

    def start(self):
        run_command(
            f"RUST_LOG=info,fnn=debug {get_project_root()}/{self.fiber_config_enum.fiber_bin_path} -c {self.tmp_path}/config.yml -d {self.tmp_path} > {self.tmp_path}/node.log 2>&1 &"
        )
        # wait rpc start
        time.sleep(2)
        print("start fiber client ")

    def stop(self):
        run_command(f"kill $(lsof -t -i:{self.rpc_port})", False)
        time.sleep(3)

    def clean(self):
        run_command("rm -rf {tmp_path}".format(tmp_path=self.tmp_path))

    def get_client(self) -> FiberRPCClient:
        return self.client

    def get_log_file(self):
        pass

    def get_peer_id(self):
        return self.client.local_node_info()["node_id"]
