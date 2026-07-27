# Contributing to Canadian MURB Geometry Analysis

Thank you for your interest in contributing to this research project.

## Development Setup

1. Clone the repository
2. Install [uv](https://docs.astral.sh/uv/) for Python package management
3. Run `make dev` to install dependencies and set up pre-commit hooks
4. Create a feature branch from `main`

## Workflow

1. Check existing issues before starting work
2. Create or reference an issue for your contribution
3. Read `AGENTS.md` for coding standards and research constraints
4. Make small, reviewable commits
5. Ensure `make lint`, `make typecheck`, and `make test` pass
6. Update relevant documentation
7. Submit a pull request with a clear description

## Code Standards

- Python 3.12+, type-annotated
- Formatted with `ruff format`
- Linted with `ruff check`
- Type-checked with `mypy`
- Tests with `pytest`

## Research Integrity

- Document all assumptions
- Preserve data provenance
- Distinguish observed from estimated values
- Report uncertainty and limitations
- Do not commit raw national datasets

## Reporting Issues

Use GitHub Issues with the provided templates. Include:
- Clear description of the problem or proposal
- Relevant context (data, configuration, environment)
- Expected versus actual behavior for bugs
