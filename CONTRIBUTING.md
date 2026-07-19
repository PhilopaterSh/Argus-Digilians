# Contributing Guide

## Overview
We welcome contributions to **Argus**. Please follow the guidelines below to ensure a smooth collaboration.

## How to Contribute
1. **Fork the repository** and create a new branch for your feature or bugfix.
2. **Write clear commit messages** adhering to the conventional commits style.
3. **Add or update tests** in the `tests/` directory.
4. **Run the full test suite** (`npm run test` or `python -m pytest`).
5. **Update documentation** (README, docs, or docs/Argus_Master_Documentation.md) as needed.
6. Submit a **Pull Request** with a concise description of your changes.

## Code Style
- Python: Follow **PEP‑8** and use `ruff` for linting.
- JavaScript/TypeScript (if any): Use **ESLint** with the Airbnb style.
- Use type hints and docstrings for all new functions/classes.

## Branch Naming
- `feature/<description>` for new features.
- `bugfix/<description>` for bug fixes.
- `docs/<description>` for documentation updates.

## Release Process
- Merge to `main` triggers CI.
- After successful CI, a maintainer will tag a new version and update `CHANGELOG.md`.

Thank you for helping improve Argus!
