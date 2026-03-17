.PHONY: test run-coverage run-coverage-html

test:
	python -W ignore::FutureWarning -m unittest discover -s tests

run-coverage:
	coverage run -W ignore::FutureWarning -m unittest discover -s tests
	coverage report

run-coverage-html:
	coverage run -W ignore::FutureWarning -m unittest discover -s tests
	coverage html
	@echo "Coverage report generated in htmlcov/index.html"
