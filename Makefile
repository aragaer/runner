.PHONY: test pypi-test pypi dist

test:
	nosetests

dist:
	rm -rf dist
	python ./setup.py sdist bdist_wheel

test-pypi: dist
	twine upload dist/* -r testpypi

pypi:
	twine upload dist/*
