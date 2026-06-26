# Contributing to Cinema Plus

Thank you for your interest in contributing to Cinema Plus! This document provides guidelines for contributing to the project.

---

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Follow the [Development Guide](docs/DEVELOPMENT.md) to set up your environment
4. Create a feature branch from `main`

---

## Development Workflow

### Branch Naming

| Type | Format | Example |
|------|--------|---------|
| Feature | `feature/description` | `feature/payment-integration` |
| Bug Fix | `fix/description` | `fix/seat-lock-timeout` |
| Documentation | `docs/description` | `docs/api-contract-update` |
| Refactor | `refactor/description` | `refactor/pricing-engine` |

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
feat: add payment gateway integration
fix: resolve seat reservation race condition
docs: update API contract for new endpoints
refactor: extract pricing logic to utility
chore: update dependencies
```

---

## Pull Request Process

1. Ensure your code follows the project's coding conventions
2. Update documentation if you're changing APIs or adding features
3. Run all verification checks before submitting:
   ```bash
   # Backend
   uvicorn backend.main:app --port 8001  # verify startup

   # Frontend
   npm run typecheck
   npm run lint
   npm run build
   ```
4. Fill out the PR template completely
5. Request review from a maintainer

---

## Code Style

### Python (Backend)
- Follow PEP 8
- Use type hints for function signatures
- Docstrings for public functions and classes

### TypeScript (Frontend)
- Strict TypeScript — no `any` types
- Functional components with hooks
- Named exports for components

---

## Reporting Issues

- Use the GitHub issue templates
- Include steps to reproduce for bugs
- For feature requests, describe the use case

---

## Code of Conduct

This project follows the [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold its standards.
