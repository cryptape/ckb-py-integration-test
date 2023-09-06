prepare:
	python -m pip install --upgrade pip
	pip install -r requirements.txt
	echo "install ckb"
	python -m download
	python -m download_ckb_light_client
	echo "install ckb cli"
	sh prepare.sh

test:
	bash test.sh test_cases/ckb2023
	bash test.sh test_cases/ckb_cli
	bash test.sh test_cases/contracts
	bash test.sh test_cases/example
	bash test.sh test_cases/framework
	bash test.sh test_cases/light_client
	bash test.sh test_cases/mocking
	#bash test.sh test_cases/node_compatible
	bash test.sh test_cases/rpc
	bash test.sh test_cases/soft_fork

clean:
	-pkill ckb
	rm -rf tmp
	rm -rf download
	rm -rf report
	rm -rf source/ckb-cli
	rm -rf source/ckb-cli-old

clean-tmp:
	-pkill ckb
	rm -rf tmp
	rm -rf report
	rm -rf ckb-cli

docs:
	python -m pytest --docs=docs/soft.md --doc-type=md test_cases/soft_fork
