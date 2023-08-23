prepare:
	python -m pip install --upgrade pip
	pip install -r requirements.txt
	echo "install ckb"
	python -m download
	python -m download_ckb_light_client
	echo "install ckb cli"
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
	python -m pytest --docs=docs/soft.md --doc-type=md test_cases/soft_fork
