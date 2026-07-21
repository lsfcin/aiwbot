# Makefile — verification contract (see code/VERIFY.md). verify-fast is free; live smoke is manual.
PY := /mnt/workspace/.venv/bin/python

verify-fast:
	$(PY) -m pytest -q tests

verify-full:
	$(PY) -m pytest -q tests

test: verify-fast

smoke:
	$(PY) proto.py

.PHONY: verify-fast verify-full test smoke
