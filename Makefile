.PHONY: test paper-artifacts paper-artifacts-strict external-corpus-artifacts figures

test:
	pytest -q
	python -m compileall -q safemap tests

paper-artifacts:
	python scripts/reproduce_paper_artifacts.py

paper-artifacts-strict:
	python scripts/reproduce_paper_artifacts.py

external-corpus-artifacts:
	python scripts/reproduce_external_corpus.py

figures:
	rsvg-convert -f pdf -o figures/safemap_conversion_pipeline.pdf figures/safemap_conversion_pipeline.svg
	rsvg-convert -f png -w 2100 -h 1120 -o figures/safemap_conversion_pipeline.png figures/safemap_conversion_pipeline.svg
