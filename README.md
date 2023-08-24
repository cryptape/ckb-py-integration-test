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

## Run single test 

you can run single test 

prepare
```shell
make prepare
```

<details>
  <summary>example</summary>

```

python -m pip install --upgrade pip
WARNING: The directory '/Users/guopenglin/Library/Caches/pip/http' or its parent directory is not owned by the current user and the cache has been disabled. Please check the permissions and owner of that directory. If executing pip with sudo, you may want sudo's -H flag.
WARNING: The directory '/Users/guopenglin/Library/Caches/pip' or its parent directory is not owned by the current user and caching wheels has been disabled. check the permissions and owner of that directory. If executing pip with sudo, you may want sudo's -H flag.
Collecting pip
  Downloading https://files.pythonhosted.org/packages/08/e3/57d4c24a050aa0bcca46b2920bff40847db79535dc78141eb83581a52eb8/pip-23.1.2-py3-none-any.whl (2.1MB)
     |████████████████████████████████| 2.1MB 894kB/s 
Installing collected packages: pip
  Found existing installation: pip 19.1.1
    Not uninstalling pip at /Library/Frameworks/Python.framework/Versions/3.7/lib/python3.7/site-packages, outside environment /Users/guopenglin/PycharmProjects/frigateDylamic/venv
    Can't uninstall 'pip'. No files were found to uninstall.
Successfully installed pip-23.1.2
pip install -r requirements.txt
WARNING: The directory '/Users/guopenglin/Library/Caches/pip' or its parent directory is not owned or is not writable by the current user. The cache has been disabled. Check the permissions and owner of that directory. If executing pip with sudo, you should use sudo's -H flag.
Requirement already satisfied: Jinja2==3.1.2 in /Users/guopenglin/PycharmProjects/frigateDylamic/venv/lib/python3.7/site-packages (from -r requirements.txt (line 1)) (3.1.2)
Requirement already satisfied: pytest==7.3.2 in /Users/guopenglin/PycharmProjects/frigateDylamic/venv/lib/python3.7/site-packages (from -r requirements.txt (line 2)) (7.3.2)
Requirement already satisfied: requests==2.31.0 in /Users/guopenglin/PycharmProjects/frigateDylamic/venv/lib/python3.7/site-packages (from -r requirements.txt (line 3)) (2.31.0)
Requirement already satisfied: tqdm==4.65.0 in /Users/guopenglin/PycharmProjects/frigateDylamic/venv/lib/python3.7/site-packages (from -r requirements.txt (line 4)) (4.65.0)
Requirement already satisfied: pytest-html==3.2.0 in /Users/guopenglin/PycharmProjects/frigateDylamic/venv/lib/python3.7/site-packages (from -r requirements.txt (line 5)) (3.2.0)
Requirement already satisfied: MarkupSafe>=2.0 in /Users/guopenglin/PycharmProjects/frigateDylamic/venv/lib/python3.7/site-packages (from Jinja2==3.1.2->-r requirements.txt (line 1)) (2.1.3)
Requirement already satisfied: iniconfig in /Users/guopenglin/PycharmProjects/frigateDylamic/venv/lib/python3.7/site-packages (from pytest==7.3.2->-r requirements.txt (line 2)) (1.1.1)
Requirement already satisfied: packaging in /Users/guopenglin/PycharmProjects/frigateDylamic/venv/lib/python3.7/site-packages (from pytest==7.3.2->-r requirements.txt (line 2)) (20.3)
Requirement already satisfied: pluggy<2.0,>=0.12 in /Users/guopenglin/PycharmProjects/frigateDylamic/venv/lib/python3.7/site-packages (from pytest==7.3.2->-r requirements.txt (line 2)) (0.13.1)
Requirement already satisfied: exceptiongroup>=1.0.0rc8 in /Users/guopenglin/PycharmProjects/frigateDylamic/venv/lib/python3.7/site-packages (from pytest==7.3.2->-r requirements.txt (line 2)) (1.1.1)
Requirement already satisfied: tomli>=1.0.0 in /Users/guopenglin/PycharmProjects/frigateDylamic/venv/lib/python3.7/site-packages (from pytest==7.3.2->-r requirements.txt (line 2)) (2.0.1)
Requirement already satisfied: importlib-metadata>=0.12 in /Users/guopenglin/PycharmProjects/frigateDylamic/venv/lib/python3.7/site-packages (from pytest==7.3.2->-r requirements.txt (line 2)) (1.6.0)
Requirement already satisfied: charset-normalizer<4,>=2 in /Users/guopenglin/PycharmProjects/frigateDylamic/venv/lib/python3.7/site-packages (from requests==2.31.0->-r requirements.txt (line 3)) (3.1.0)
Requirement already satisfied: idna<4,>=2.5 in /Library/Frameworks/Python.framework/Versions/3.7/lib/python3.7/site-packages (from requests==2.31.0->-r requirements.txt (line 3)) (2.8)
Requirement already satisfied: urllib3<3,>=1.21.1 in /Users/guopenglin/PycharmProjects/frigateDylamic/venv/lib/python3.7/site-packages (from requests==2.31.0->-r requirements.txt (line 3)) (1.24.1)
Requirement already satisfied: certifi>=2017.4.17 in /Library/Frameworks/Python.framework/Versions/3.7/lib/python3.7/site-packages (from requests==2.31.0->-r requirements.txt (line 3)) (2019.3.9)
Requirement already satisfied: py>=1.8.2 in /Users/guopenglin/PycharmProjects/frigateDylamic/venv/lib/python3.7/site-packages (from pytest-html==3.2.0->-r requirements.txt (line 5)) (1.11.0)
Requirement already satisfied: pytest-metadata in /Library/Frameworks/Python.framework/Versions/3.7/lib/python3.7/site-packages (from pytest-html==3.2.0->-r requirements.txt (line 5)) (1.8.0)
Requirement already satisfied: zipp>=0.5 in /Users/guopenglin/PycharmProjects/frigateDylamic/venv/lib/python3.7/site-packages (from importlib-metadata>=0.12->pytest==7.3.2->-r requirements.txt (line 2)) (3.1.0)
Requirement already satisfied: pyparsing>=2.0.2 in /Users/guopenglin/PycharmProjects/frigateDylamic/venv/lib/python3.7/site-packages (from packaging->pytest==7.3.2->-r requirements.txt (line 2)) (2.4.7)
Requirement already satisfied: six in /Library/Frameworks/Python.framework/Versions/3.7/lib/python3.7/site-packages (from packaging->pytest==7.3.2->-r requirements.txt (line 2)) (1.12.0)
echo "install ckb"
install ckb
python -m download
system:Darwin,architecture:x86_64
Downloading URL: https://github.com/nervosnetwork/ckb/releases/download/v0.109.0/ckb_v0.109.0_aarch64-apple-darwin-portable.zip
100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 22.5M/22.5M [00:02<00:00, 10.6MiB/s]
system:Darwin,architecture:x86_64
Downloading URL: https://github.com/nervosnetwork/ckb/releases/download/v0.110.0/ckb_v0.110.0_aarch64-apple-darwin-portable.zip
100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 22.5M/22.5M [00:01<00:00, 18.0MiB/s]
system:Darwin,architecture:x86_64
Downloading URL: https://github.com/nervosnetwork/ckb/releases/download/v0.111.0-rc6/ckb_v0.111.0-rc6_aarch64-apple-darwin-portable.zip
100%|██████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 22.6M/22.6M [00:04<00:00, 5.37MiB/s]
echo "install ckb cli"
install ckb cli
sh prepare.sh
fatal: destination path 'ckb-cli' already exists and is not an empty directory.
Already on 'exec/data2'
Your branch is up to date with 'origin/exec/data2'.
cargo build --release
    Finished release [optimized] target(s) in 0.70s
```
</details>

run single test 

```shell
# if not set debugging ,will generated html file in report/report.html
python -m pytest test_cases/node_compatible/test_after_ckb_2023_hardfork.py::TestAfterCkb2023::test_node_sync

```
<details>
  <summary>example</summary>

```
(venv) @MacBook-Pro-4 ckb-py-integration-test % python -m pytest test_cases/node_compatible/test_after_ckb_2023_hardfork.py::TestAfterCkb2023::test_node_sync

========================================================================== test session starts ==========================================================================
platform darwin -- Python 3.7.3, pytest-7.3.2, pluggy-0.13.1
rootdir: /Users/WebstormProjects/ckb-py-integration-test
configfile: pytest.ini
plugins: html-3.2.0, allure-pytest-2.9.45, forked-1.0.2, xdist-1.28.0, cov-2.7.1, tap-2.3, metadata-1.8.0
collected 1 item                                                                                                                                                        

test_cases/node_compatible/test_after_ckb_2023_hardfork.py 

.                                                                                                      [100%]

----------------------------- generated html file: file:///Users/WebstormProjects/ckb-py-integration-test/report/report.html -----------------------------
===================================================================== 1 passed in 62.97s (0:01:02) ======================================================================
```

</details>

clean tmp dir
```angular2html

make clean-tmp
```
<details>
  <summary>example</summary>

```angular2html
pkill ckb
make: [clean-tmp] Error 1 (ignored)
rm -rf tmp
rm -rf report
```
</details>

## Debugging

You can add debug logging for pytest by modifying the [pytest.ini](pytest.ini) file:

```angular2html
addopts = -s 
```

## Contributing

If you want to contribute to this project, you can fork this repository, create a feature branch, and send us a Pull Request. For more information, please see the CONTRIBUTING.md file.
