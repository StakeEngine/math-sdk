PYTHON := python3
VENV_DIR := env
VENV_PY := $(VENV_DIR)/bin/python
TEST_NAMES = 0_0_cluster 0_0_scatter 0_0_lines 0_0_expwilds 0_0_ways 0_0_lines_feature_match

ifeq ($(OS),Windows_NT)
	VENV_PY := $(VENV_DIR)\Scripts\python.exe
	ACTIVATE := $(VENV_DIR)\Scripts\activate.bat
else
	ACTIVATE := source $(VENV_DIR)/bin/activate
endif

makeVirtual:
	$(PYTHON) -m venv $(VENV_DIR)

pipInstall: makeVirtual
	$(VENV_PY) -m pip install --upgrade pip

pipPackages: pipInstall
	$(VENV_PY) -m pip install -r requirements.txt

packInstall: pipPackages
	$(VENV_PY) -m pip install -e .

setup: packInstall
	@echo "Virtual environment ready."
	@echo "To activate it, run:"
	@echo "$(ACTIVATE)"


run GAME:
	$(VENV_PY) games/$(GAME)/run.py
	@echo "Checking compression setting..."
	@if grep -q "compression = False" games/$(GAME)/run.py; then \
		echo "Compression is disabled, formatting books files..."; \
		$(VENV_PY) utils/format_books_json.py games/$(GAME) || echo "Warning: Failed to format books files"; \
	else \
		echo "Compression is enabled, skipping formatting."; \
	fi

test:
	cd $(CURDIR)
	pytest tests/

test_run:
	@for f in $(TEST_NAMES); do \
		echo "processing $$f"; \
		$(VENV_PY) games/$$f/run.py; \
	done


clean:
	rm -rf env __pycache__ *.pyc