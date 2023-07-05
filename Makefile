prepare:
	python -m pip install --upgrade pip
	pip install -r requirements.txt
	echo "install ckb"
	python -m download
	echo "install ckb cli"
	sh prepare.sh

test:
	python -m pytest

clean:
	pkill ckb
	rm -rf tmp
	rm -rf download
	rm -rf report
	rm -rf source/ckb-cli
	rm -rf ckb-cli
