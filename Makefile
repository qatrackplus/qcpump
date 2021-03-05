cover:
	py.test --cov-report term-missing --cov ./ ${args}

docs:
	cd docs && make html

docs-autobuild:
	sphinx-autobuild docs docs/_build/html --port 8009


.PHONY: docs-autobuild docs cover

