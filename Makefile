# After editing resume.yaml, build resume.pdf:
#   make pdf

VENV := .venv
PY := $(VENV)/bin/python

.PHONY: pdf install

$(VENV)/.installed: requirements.txt
	python3 -m venv $(VENV)
	$(PY) -m pip install -r requirements.txt
	touch $@

install: $(VENV)/.installed

pdf: install
	$(PY) build.py
