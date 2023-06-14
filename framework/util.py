from jinja2 import Environment, FileSystemLoader, select_autoescape
import subprocess
import time
import json
import os


def to_json(value):
    return json.dumps(value)


def to_remove_str(value):
    return value[1:-1]


CKB_MINER_CONFIG = {
    'd': ''
}


# ckb config ,ckb miner config ,ckb spec config
def get_ckb_configs(p2p_port, rpc_port, spec='{ file = "dev.toml" }'):
    return {
               # 'ckb_chain_spec': '{ bundled = "specs/mainnet.toml" }',
               'ckb_chain_spec': spec,
               'ckb_network_listen_addresses': ["/ip4/0.0.0.0/tcp/{p2p_port}".format(p2p_port=p2p_port)],
               'ckb_rpc_listen_address': '127.0.0.1:{rpc_port}'.format(rpc_port=rpc_port),
               'ckb_rpc_modules': ["Net", "Pool", "Miner", "Chain", "Stats", "Subscription", "Experiment", "Debug"],
               'ckb_block_assembler_code_hash': '0x9bd7e06f3ecf4be0f2fcd2188b23f1b9fcc88e5d4b65a8637b17723bbda3cce8',
               'ckb_block_assembler_args': '0x8883a512ee2383c01574a328f60eeccbb4d78240',
               'ckb_block_assembler_hash_type': 'type',
               'ckb_block_assembler_message': '0x'
           }, {
               'ckb_miner_rpc_url': '127.0.0.1:{rpc_port}'.format(rpc_port=rpc_port),
               'ckb_chain_spec': spec,
           }, {}


def create_config_file(config_values, template_path, output_file):
    file_loader = FileSystemLoader(get_project_root())
    # 创建一个环境
    env = Environment(
        loader=file_loader,
        autoescape=select_autoescape(['html', 'xml'])
    )
    # 添加新的过滤器
    env.filters['to_json'] = to_json
    env.filters['to_remove_str'] = to_remove_str
    # 加载模板
    template = env.get_template(template_path)

    if not os.path.exists(os.path.dirname(output_file)):
        os.makedirs(os.path.dirname(output_file))

    # 使用数据渲染模板
    output = template.render(**config_values)

    # 将渲染的模板写入文件
    with open(output_file, 'w') as f:
        f.write(output)


def run_command(cmd):
    if cmd[-1] == "&":
        cmd1 = "{cmd} echo $! > pid.txt".format(cmd = cmd)
        print("cmd:{cmd}".format(cmd=cmd1))

        subprocess.Popen(cmd1, shell=True)
        time.sleep(1)
        with open("pid.txt", "r") as f:
            pid = int(f.read().strip())
            print("PID:", pid)
            return pid

    print("cmd:{cmd}".format(cmd=cmd))
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout, stderr = process.communicate()
    if stderr.decode('utf-8') != "":
        print("result:{result}".format(result=stderr.decode('utf-8')))
        return stderr.decode('utf-8')
    print("result:{result}".format(result=stdout.decode('utf-8')))
    return stdout.decode('utf-8')


def get_project_root():
    current_path = os.path.dirname(os.path.abspath(__file__))
    return "{path}/ckb-py-integration-test".format(path=current_path.split("/ckb-py-integration-test")[0])