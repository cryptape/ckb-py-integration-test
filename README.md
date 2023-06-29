```
# ckb-py-integration-test

ckb-py-integration-test 是一个使用 Python 进行集成测试的项目，目标是自动化 CKB 链上操作的测试。

## 依赖

此项目需要在系统上安装 Python 和 pip。此项目所需的 Python 库在 `requirements.txt` 中列出，可以通过运行以下命令来安装：

make prepare

这条 `prepare` 命令将执行以下操作：

1. 安装在 `requirements.txt` 中列出的 Python 库。
2. 下载并安装 ckb 二进制文件。
3. 下载并安装 ckb-cli。

此外，我们还提供了以下命令：

- 执行项目的测试：

    make test

- 清理临时文件和其他生成的项目文件：

    make clean

## 参与贡献

如果你想为此项目贡献代码，你可以 fork 这个仓库，创建特性分支，并向我们发送拉取请求（Pull Request）。有关详细信息，请查看 CONTRIBUTING.md 文件。
```
=======
# ckb-py-integration-test

ckb-py-integration-test is a project that uses Python for integrated testing. The goal is to automate the testing of operations on the CKB chain.

## Dependencies

This project requires Python and pip to be installed on your system. The Python libraries needed for this project are listed in `requirements.txt`. You can install them by running the following command:
```
make prepare
```
This `prepare` command will perform the following operations:

1. Install the Python libraries listed in `requirements.txt`.
2. Download and install the ckb binary.
3. Download and install the ckb-cli.

In addition, we also provide the following commands:

- To run the tests for the project:
  
```
    make test
```

- To clean up temporary files and other generated project files:
```
    make clean
```
## Debugging

You can add debug logging for pytest by modifying the [pytest.ini](pytest.ini) file:

```angular2html
addopts = -s 
```

## Contributing

If you want to contribute to this project, you can fork this repository, create a feature branch, and send us a Pull Request. For more information, please see the CONTRIBUTING.md file.
