#!/bin/bash

echo "Running code quality checks..."

# Run Black formatter
echo "Running Black..."
black . || exit 1

# Run isort
echo "Running isort..."
isort . || exit 1

# Run Flake8
echo "Running Flake8..."
flake8 . || exit 1

# Run tests
echo "Running tests..."
pytest || exit 1

echo "All checks passed!" 