# ckb-py-integration-test

ckb-py-integration-test is a project that uses Python for integrated testing. The goal is to automate the testing of operations on the CKB chain.

## Dependencies

This project requires Python and pip to be installed on your system. The Python libraries needed for this project are listed in `requirements.txt`. You can install them by running the following command:

make prepare

This `prepare` command will perform the following operations:

1. Install the Python libraries listed in `requirements.txt`.
2. Download and install the ckb binary.
3. Download and install the ckb-cli.

In addition, we also provide the following commands:

- To run the tests for the project:

    make test

- To clean up temporary files and other generated project files:

    make clean

## Debugging

You can add debug logging for pytest by modifying the [pytest.ini](pytest.ini) file:

```angular2html
addopts = -s 
```

## Contributing

If you want to contribute to this project, you can fork this repository, create a feature branch, and send us a Pull Request. For more information, please see the CONTRIBUTING.md file.