.PHONY: test lint type-check format clean

test:
	pytest

test-cov:
	pytest --cov=src --cov-report=html

lint:
	flake8 src tests
	black --check src tests
	isort --check-only src tests

type-check:
	mypy src tests

format:
	black src tests
	isort src tests

clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type d -name "*.egg-info" -exec rm -r {} +
	find . -type d -name ".mypy_cache" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name "htmlcov" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete 