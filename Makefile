ifeq ($(OS), Windows_NT)
	PYTHON = python
	VENV_PY = env\Scripts\python
else
	PYTHON = python3
	VENV_PY = ./env/bin/python3
endif 

.PHONY: setup run test clean 

makeVirtual:
	$(PYTHON) -m venv env 

pipInstall: makeVirtual
	$(VENV_PY) -m pip install --upgrade pip

pipPackages: pipInstall
	$(VENV_PY) -m pip install -r requirements.txt

packInstall: pipPackages
	$(VENV_PY) -m pip install -e .

setup: packInstall

run GAME:
	$(VENV_PY) games/$(GAME)/run.py
	@echo "Checking compression setting..."
	@if grep -q "compression = False" games/$(GAME)/run.py; then \
		echo "Compression is disabled, formatting books files..."; \
		$(VENV_PY) scripts/format_books_json.py games/$(GAME) || echo "Warning: Failed to format books files"; \
	else \
		echo "Compression is enabled, skipping formatting."; \
	fi

test:
	cd $(CURDIR)
	pytest tests/

clean:
	rm -rf env __pycache__ *.pyc