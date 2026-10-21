# Default recipe to display help
default:
  @just --list

# Sync all dependency groups into the project environment
sync:
  uv sync --all-groups

# Format code and markdown, then auto-fix lint findings
format:
  rumdl fmt .
  uv run ruff format .
  uv run ruff check --fix .

# Auto-fix what plain formatting cannot: markdown lint and ruff findings
fix:
  rumdl check --fix .
  uv run ruff check --fix .

# Run every lint gate: spelling, markdown, ruff, and type checks
lint:
  typos
  rumdl check .
  uv run ruff check .
  uv run ruff format --check .
  uv run ty check src tests

# Run the pytest suite (example tests plus Hypothesis property tests)
test:
  uv run pytest

# Run the full pytest suite (same scope as test; kept for CI compatibility)
test-all:
  uv run pytest

# Run tests with a coverage report
test-coverage:
  uv run pytest --cov=autoresearch --cov-report=term-missing --cov-report=html

# Run the pytest benchmark suite
bench:
  uv run pytest -m benchmark --benchmark-only

# Build the sdist and wheel
build:
  uv build

# Type check the package and the test suite
typecheck:
  uv run ty check src tests

# Fail if Chinese characters appear outside the intentionally Chinese design doc
check-cn:
  @ if rg --line-number --column "\p{Han}" src tests README.md AGENTS.md; then echo "Chinese characters found"; exit 1; fi

# Run the full CI gate
ci: lint test build

# ============================================================
# Maintenance & Tools
# ============================================================

# Remove build artifacts and tool caches
clean:
  rm -rf dist/ .pytest_cache/ .ruff_cache/ htmlcov/ .coverage
  find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
  find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

# Install the dev dependencies plus the lint tools this Justfile calls
setup:
  uv sync --all-groups
  uv tool install rumdl
  cargo install typos-cli

# Refresh the dependency lock file
lock:
  uv lock

# Upgrade every locked dependency
update:
  uv lock --upgrade
