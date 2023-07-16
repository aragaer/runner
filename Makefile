.PHONY: test pypi-test pypi dist flake

test:
	@nose2

dist:
	rm -rf dist
	python ./setup.py sdist

test-pypi: dist
	twine upload dist/* -r testpypi

pypi:
	twine upload dist/*

flake:
	@flake8
