# Contributing to Telegram Print Bot

Thank you for your interest in contributing to the Telegram Print Bot! This document provides guidelines for contributing to the project.

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct/). By participating, you are expected to uphold this code.

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include:

- **Clear description** of the issue
- **Steps to reproduce** the problem
- **Expected behavior** vs actual behavior
- **Environment details**:
  - OS and version
  - Docker version
  - Printer model and IP
  - Bot configuration (without sensitive data)
- **Log output** (with sensitive data removed)

### Suggesting Features

Feature suggestions are welcome! Please:

1. Check if the feature already exists or is planned
2. Describe the use case and benefits
3. Consider implementation complexity
4. Provide mockups or examples if applicable

### Code Contributions

#### Development Setup

1. **Fork and clone the repository**:
   ```bash
   git clone https://github.com/lewkoo/telegram-printer-bot.git
   cd telegram-printer-bot
   ```

2. **Set up development environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your test configuration
   ```

3. **Build and test locally**:
   ```bash
   docker compose up --build
   ```

#### Code Style

- **Python**: Follow PEP 8 style guidelines
- **Type hints**: Use type annotations for all functions
- **Docstrings**: Document all modules, classes, and functions
- **Comments**: Explain complex logic and business decisions
- **Logging**: Use appropriate log levels (DEBUG, INFO, WARNING, ERROR)

#### Testing

- Test with your actual printer setup
- Verify both PDF and Office document printing (if LibreOffice enabled)
- Test quiet hours functionality
- Ensure Ukrainian translations work correctly
- Test error handling and edge cases

#### Commit Guidelines

- Use clear, descriptive commit messages
- Reference issues and pull requests when applicable
- Keep commits focused on single changes
- Use conventional commit format when possible:
  ```
  feat: add support for new printer model
  fix: resolve quiet hours timezone issue
  docs: update deployment instructions
  ```

#### Pull Request Process

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the code style guidelines

3. **Test thoroughly** with your setup

4. **Update documentation** if needed:
   - README.md for user-facing changes
   - DEPLOYMENT.md for setup changes
   - Code comments for implementation details

5. **Submit pull request** with:
   - Clear title and description
   - Link to related issues
   - Screenshots/logs if applicable
   - Test results

6. **Address review feedback** promptly

## Development Areas

### High Priority
- **Printer compatibility**: Testing with different printer models
- **Error handling**: Improving robustness and user feedback
- **Documentation**: User guides and troubleshooting
- **Security**: Access control and input validation

### Medium Priority
- **Features**: Advanced print options, multi-printer support
- **Performance**: Optimization for high-volume usage
- **Monitoring**: Health checks and metrics
- **Deployment**: Additional platform support

### Low Priority
- **UI improvements**: Better user interface elements
- **Internationalization**: Additional language support
- **Integration**: External service connections

## Project Structure

```
telegram-print-bot/
├── src/                    # Python source code
│   ├── bot.py             # Main bot application
│   ├── printing.py        # Printing functionality
│   └── requirements.txt   # Python dependencies
├── .github/               # GitHub workflows
├── data/                  # Runtime data directory
├── artifacts/             # Build artifacts
├── Dockerfile             # Container definition
├── docker-compose.yml     # Local development setup
├── docker-entrypoint.sh   # Container startup script
├── unraid-template.xml    # Unraid deployment template
└── docs/                  # Additional documentation
```

## Technical Guidelines

### Printer Support

When adding support for new printers:

1. **Test IPP compatibility** first
2. **Document specific requirements** (drivers, settings)
3. **Update printer compatibility list** in README.md
4. **Consider fallback options** for edge cases

### Error Handling

- **Log errors** appropriately without exposing sensitive data
- **Provide user-friendly messages** in both English and Ukrainian
- **Handle network timeouts** gracefully
- **Validate user input** before processing

### Security Considerations

- **Never log sensitive data** (tokens, user IDs in full)
- **Validate file types** before processing
- **Implement rate limiting** for API calls
- **Use secure defaults** for configuration

## Getting Help

- **Documentation**: Check README.md and DEPLOYMENT.md first
- **Issues**: Search existing issues for similar problems
- **Discussions**: Use GitHub Discussions for general questions
- **Community**: Join project discussions and help others

## Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes for significant contributions
- GitHub contributor statistics

Thank you for helping make this project better! 🚀
