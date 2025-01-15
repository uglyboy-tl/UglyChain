# Development Guide

## Setup Development Environment

1. Clone repository:
   ```bash
   git clone https://github.com/uglychain/uglychain.git
   cd uglychain
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

3. Configure pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Running Tests

Run all tests:
```bash
pytest tests/
```

Run specific test module:
```bash
pytest tests/test_llm.py
```

Run with coverage report:
```bash
pytest --cov=src tests/
```

## Code Style

- Follow PEP 8 style guide
- Use black for code formatting
- Use isort for import sorting
- Use flake8 for linting

## Contributing

1. Create a new branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and commit:
   ```bash
   git add .
   git commit -m "feat: your feature description"
   ```

3. Push your branch:
   ```bash
   git push origin feature/your-feature-name
   ```

4. Create a pull request on GitHub
