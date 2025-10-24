.PHONY: test coverage coverage-html

test:
	python -m unittest discover -s tests

coverage:
	coverage run -m unittest discover -s tests
	coverage report

coverage-html:
	coverage run -m unittest discover -s tests
	coverage html
	@echo "Coverage report generated in htmlcov/index.html"
