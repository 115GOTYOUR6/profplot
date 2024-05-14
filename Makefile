PY=python3
PIP=pip
VENV_NAME=vir_profplot
TEST_DIRS=./tests

.PHONEY: run_all_tests

run_all_tests:
	for dir in $(TEST_DIRS); do \
		$(PY) -m unittest discover -s $$dir -p "test*"; \
		done;
