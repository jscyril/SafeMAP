.PHONY: test paper-artifacts paper-artifacts-strict

test:
	pytest -q
	python -m compileall -q safemap tests

paper-artifacts:
	python scripts/reproduce_paper_artifacts.py

paper-artifacts-strict:
	python scripts/reproduce_paper_artifacts.py --strict-denominators
