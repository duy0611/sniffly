# Agent Instructions

## Package Manager
Use **pip** for Python dependencies: `pip install -e .` for local development

Python package manager (not npm) - this is a Python CLI tool with FastAPI backend

## Python Environment
Use **pyenv** + **venv** for isolated environment:
- Python version: 3.12.8 (defined in `.python-version`)
- Virtual environment: `.venv/` (created by `make setup`)
- Activate: `source .venv/bin/activate`

## Commit Attribution
AI commits MUST include:
```
Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

## Key Conventions

### Project Structure
- `sniffly/` - Main Python package (CLI, API, core processing)
- `sniffly-site/` - Static site for shared dashboards (minimal Node.js, mostly Python)
- `tests/` - Test suite with mock data
- `docs/` - Documentation files

### Python Standards
- Python 3.10+ required
- Use ruff for linting: `./lint.sh`
- Type hints checked with mypy (but `disallow_untyped_defs = false`)
- Line length: 120 chars
- Test files: allow print and asserts (T201, S101)

### Testing
Run tests: `python run_tests.py`

### CLI Commands
Main entry point: `sniffly` command (defined in `sniffly.cli:cli`)

| Command | Description |
|---------|-------------|
| `sniffly init` | Start analytics dashboard server |
| `sniffly config set <key> <value>` | Set configuration |
| `sniffly config show` | Show current config |
| `sniffly help` | Show help |

### Development Setup
**Recommended**: Use pyenv + venv + Makefile:
```bash
make setup        # Complete setup (creates .venv + installs dependencies)
make shell        # Activate virtual environment in new shell (easy way)
# OR
source .venv/bin/activate  # Activate in current shell (manual way)

# Then run:
make serve        # Start dashboard server
make test         # Run tests
make lint         # Run linter
make clean        # Clean build artifacts
make clean-venv   # Remove virtual environment
```

Manual setup with pyenv + venv:
```bash
# Python version is defined in .python-version file
pyenv local $(cat .python-version)
python -m venv .venv
source .venv/bin/activate
pip install -e .
pip install -r requirements-dev.txt
```

Without pyenv:
```bash
pip install -e .              # Install for development
pip install -r requirements-dev.txt  # Install dev dependencies
python run_tests.py           # Run tests
./lint.sh                     # Lint
```

### API Structure
FastAPI application in `sniffly/server.py`
- Routes in `sniffly/api/` (data.py, messages.py)
- Core processing in `sniffly/core/` (processor.py, stats.py)
- Utils in `sniffly/utils/` (caching, logging, pricing)

### Configuration
- Config stored in `~/.sniffly/config.json`
- Default port: 8081
- Default host: 127.0.0.1
- See `sniffly/config.py` for config management
