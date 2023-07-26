prepare:
	python -m pip install --upgrade pip
	pip install -r requirements.txt
	echo "install ckb"
	python -m download
	echo "install ckb cli and new ckb"
	sh prepare.sh

test:
	python -m pytest

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
	python -m pytest --docs=docs/tx_pool_refactor.md --doc-type=md test_cases/tx_pool_refactor
	python -m pytest --docs=docs/ckb2023.md --doc-type=md test_cases/ckb2023
