.PHONY: test paper-artifacts paper-artifacts-strict external-corpus-artifacts

test:
	pytest -q
	python -m compileall -q safemap tests

paper-artifacts:
	python scripts/reproduce_paper_artifacts.py

paper-artifacts-strict:
	python scripts/reproduce_paper_artifacts.py

external-corpus-artifacts:
	python scripts/reproduce_external_corpus.py
