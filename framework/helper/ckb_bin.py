from framework.util import run_command
from framework.util import get_project_root


def version(ckb_version: str, verbose: bool):
    """
    根据verbose参数决定命令格式。
    当verbose为True时，使用 --version；
    当verbose为False时，使用 -V。

    :param verbose: 如果为True，使用--version；否则使用-V
    :return: 命令执行结果

    Args:
        ckb_version:
    """
    ckb_bin_path = f"cd {get_project_root()}/{ckb_version} && ./ckb"
    command = "--version" if verbose else "-V"
    cmd = "{ckb_bin} {command}".format(ckb_bin=ckb_bin_path, command=command)
    return run_command(cmd)


def run():
    """

    Returns:

    """
    cmd = "{ckb_bin} run".format(ckb_bin=ckb_bin_path)
    return run_command(cmd)
