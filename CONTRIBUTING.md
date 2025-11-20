# Contributing to IDF Creator

Thank you for your interest in contributing to IDF Creator! This document provides guidelines and instructions for contributing to the project.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Code Style](#code-style)
- [Areas for Contribution](#areas-for-contribution)

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Respect different viewpoints and experiences

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/idf-creator.git
   cd idf-creator
   ```
3. **Add the upstream remote**:
   ```bash
   git remote add upstream https://github.com/original-owner/idf-creator.git
   ```

## Development Setup

1. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -e .  # Install in development mode
   ```

3. **Install optional dependencies** (for full functionality):
   - Tesseract OCR for image parsing
   - EnergyPlus for running simulations

## Project Structure

```
idf-creator/
├── src/                    # Main source code
│   ├── core/              # Core IDF generation logic
│   ├── validation/        # Validation modules
│   ├── compliance/        # Compliance checking
│   ├── utils/             # Utility functions
│   └── ...                # Other modules
├── tests/                  # Test files
│   ├── data/             # Test data files
│   └── test_*.py         # Test modules
├── examples/              # Example scripts and usage
├── scripts/               # Utility scripts
│   └── archive/          # Historical/one-off scripts
├── docs/                  # Documentation
│   ├── history/         # Historical documentation
│   └── *.md             # Current documentation
├── main.py               # Main entry point
├── requirements.txt      # Python dependencies
└── README.md            # Project README
```

## Making Changes

1. **Create a new branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

2. **Make your changes** following the code style guidelines

3. **Write or update tests** for your changes

4. **Test your changes**:
   ```bash
   python -m pytest tests/
   ```

5. **Update documentation** if needed

## Testing

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_validation.py

# Run with verbose output
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=src
```

### Writing Tests

- Place test files in the `tests/` directory
- Name test files with `test_` prefix (e.g., `test_validation.py`)
- Use descriptive test function names
- Include both unit tests and integration tests
- Test edge cases and error conditions

Example test structure:
```python
import pytest
from src.module import function

def test_function_basic():
    """Test basic functionality."""
    result = function(input)
    assert result == expected

def test_function_edge_case():
    """Test edge case handling."""
    with pytest.raises(ValueError):
        function(invalid_input)
```

## Submitting Changes

1. **Commit your changes** with clear, descriptive commit messages:
   ```bash
   git commit -m "Add feature: description of what you added"
   ```

2. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Create a Pull Request** on GitHub:
   - Provide a clear title and description
   - Reference any related issues
   - Include screenshots or examples if applicable
   - Ensure all tests pass

4. **Respond to feedback** and make requested changes

## Code Style

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write docstrings for all functions and classes
- Keep functions focused and small
- Use meaningful variable and function names

Example:
```python
def generate_idf_file(
    address: str,
    building_type: str = "Office",
    floor_area: float = None
) -> str:
    """
    Generate an EnergyPlus IDF file from building information.
    
    Args:
        address: Building street address
        building_type: Type of building (Office, Residential, etc.)
        floor_area: Total floor area in square meters
        
    Returns:
        Path to generated IDF file
        
    Raises:
        ValueError: If address is invalid
    """
    # Implementation
    pass
```

## Areas for Contribution

We welcome contributions in these areas:

### 🐛 Bug Fixes
- Fix issues reported in GitHub Issues
- Improve error handling and validation
- Fix compatibility issues

### ✨ New Features
- Enhanced document parsing (PDFs, images)
- Additional building type templates
- More HVAC system types
- Better geometry estimation
- Integration with building databases

### 📚 Documentation
- Improve README and guides
- Add code examples
- Write tutorials
- Translate documentation

### 🧪 Testing
- Increase test coverage
- Add integration tests
- Add performance benchmarks
- Add validation tests

### 🔧 Code Quality
- Refactor for better maintainability
- Improve performance
- Add type hints
- Improve error messages

### 🌍 Internationalization
- Support for non-US locations
- Additional climate zones
- Local building standards

## Questions?

- Open an issue for bug reports or feature requests
- Check existing issues and discussions
- Review the documentation in `docs/`

Thank you for contributing to IDF Creator! 🎉

