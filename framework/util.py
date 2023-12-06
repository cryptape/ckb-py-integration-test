from jinja2 import Environment, FileSystemLoader, select_autoescape
import subprocess
import time
import json
import toml
import os, re


def to_json(value):
    return json.dumps(value)


def to_remove_str(value):
    return value[1:-1]


# ckb config ,ckb miner config ,ckb spec config
def get_ckb_configs(p2p_port, rpc_port, spec='{ file = "dev.toml" }'):
    return {
        # 'ckb_chain_spec': '{ bundled = "specs/mainnet.toml" }',
        'ckb_chain_spec': spec,
        'ckb_network_listen_addresses': ["/ip4/0.0.0.0/tcp/{p2p_port}".format(p2p_port=p2p_port)],
        'ckb_rpc_listen_address': '127.0.0.1:{rpc_port}'.format(rpc_port=rpc_port),
        'ckb_rpc_modules': ["Net", "Pool", "Miner", "Chain", "Stats", "Subscription", "Experiment", "Debug",
                            "IntegrationTest", "Indexer"],
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


def run_command(cmd, check_exit_code=True):
    if cmd[-1] == "&":
        cmd1 = "{cmd} echo $! > pid.txt".format(cmd=cmd)
        print("cmd:{cmd}".format(cmd=cmd1))

        process = subprocess.Popen(cmd1, shell=True)
        time.sleep(1)
        print("process PID:", process.pid)
        with open("pid.txt", "r") as f:
            pid = int(f.read().strip())
            print("PID:", pid)
            # pid is new shell
            # pid+1 = run cmd
            # result:       55456  13.6  0.2 409387712  34448   ??  R     4:22PM   0:00.05 ./ckb run --indexer
            #        55457   5.8  0.0 34411380   2784   ??  S     4:22PM   0:00.02 /bin/sh -c ps aux | grep ckb
            #        55459   0.0  0.0 33726716   1836   ??  R     4:22PM   0:00.01 grep ckb
            #        55455   0.0  0.0 438105996   1508   ??  S     4:22PM   0:00.01 \
            #        /bin/sh -c cd /Users/guopenglin/WebstormProjects/gp/ckb-py-integration-test/tmp/node/node && \
            #        ./ckb run --indexer > node.log 2>&1 & echo $! > pid.txt
            return pid + 1

    print("cmd:{cmd}".format(cmd=cmd))
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout, stderr = process.communicate()
    exit_code = process.returncode

    if exit_code != 0:
        print("Command failed with exit code:", exit_code)
        if stderr:
            print("Error:", stderr.decode('utf-8'))
        if not check_exit_code:
            return exit_code
        raise Exception(stderr.decode('utf-8'))
    if stderr.decode('utf-8') != "" and stdout.decode('utf-8') != "":
        print("wain:{result}".format(result=stderr.decode('utf-8')))
        print("result:{result}".format(result=stdout.decode('utf-8')))
        return stdout.decode('utf-8')
    print("result:{result}".format(result=stdout.decode('utf-8')))
    return stdout.decode('utf-8')


def get_project_root():
    current_path = os.path.dirname(os.path.abspath(__file__))
    pattern = r"(.*ckb-py-integration-test)"
    matches = re.findall(pattern, current_path)
    if matches:
        root_dir = max(matches, key=len)
        return root_dir
    else:
        raise Exception("not found ckb-py-integration-test dir")


def read_toml_file(file_path):
    try:
        with open(file_path, "r") as file:
            toml_content = file.read()
            config = toml.loads(toml_content)
            return config
    except Exception as e:
        print(f"Error reading TOML file: {e}")
        return None
