prepare:
	python3 -m venv venv
	. venv/bin/activate
	python3 -m pip install --upgrade pip
	pip install -r requirements.txt
	echo "install ckb"
	python3 -m download

	python3 -m download_ckb_light_client
	echo "install ckb cli"
	sh prepare.sh

check_failed_html:
	@if test -n "$$(ls report/*failed.html 2>/dev/null)"; then \
        echo "Error: Failed HTML files found in the 'report' directory"; \
        exit 1; \
    fi

test_cases := \
    test_cases/replace_rpc \
    test_cases/ckb_cli

.PHONY: test
test:
	@failed_cases=; \
    for test_case in $(test_cases); do \
        echo "Running tests for $$test_case"; \
        if ! bash test.sh "$$test_case"; then \
            failed_cases+="$$test_case "; \
        fi; \
    done; \
    if [ -n "$$failed_cases" ]; then \
        echo "Some test cases failed: $$failed_cases"; \
        exit 1; \
    fi

clean:
	pkill ckb
	rm -rf tmp
	rm -rf download
	rm -rf report
	rm -rf source/ckb-cli*
	rm -rf ckb-*

docs:
	python -m pytest --docs=docs/soft.md --doc-type=md test_cases/soft_fork