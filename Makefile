cover:
	py.test --cov-report term-missing --cov ./ ${args}

cover-module:
	py.test --cov-report term-missing --cov ./${module} ${module}

docs:
	cd docs && make html

docs-autobuild:
	sphinx-autobuild docs docs/_build/html --port 8099

pyinstaller:
	pyinstaller .\qcpump.spec


.PHONY: docs-autobuild docs cover cover-module pyinstaller

