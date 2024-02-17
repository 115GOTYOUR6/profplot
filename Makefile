PY=python3
TEST_DIRS=./tests

run_all_tests:
	for dir in $(TEST_DIRS); do \
		$(PY) -m unittest discover -s $$dir -p "test*"; \
		done;
