# Static Code Analysis Framework for Embedded C/C++

[![CI](https://github.com/yourorg/static-analyzer/workflows/CI/badge.svg)](https://github.com/yourorg/static-analyzer/actions)
[![Coverage](https://img.shields.io/badge/coverage-95%25-green.svg)](https://github.com/yourorg/static-analyzer)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A production-quality static analysis framework for Embedded C/C++ projects, designed for automotive and safety-critical applications. **Now featuring automated GitHub integration with LLM-powered analysis workflows via Model Context Protocol (MCP).**

## Features

- **AST-based Analysis**: Uses Clang/libclang for precise C/C++ parsing
- **MISRA C:2012 & CERT C/C++**: Built-in rule implementations
- **Deterministic Results**: Reproducible, audit-ready outputs
- **CI/CD Integration**: GitHub Actions workflow included
- **Deviation Management**: YAML-based rule suppression with justification
- **AI-Assisted Explanations**: Optional GenAI for human-readable insights
- **Extensible Architecture**: Easy to add custom rules
- **🚀 NEW: GitHub MCP Integration**: Automated commit analysis with LLM workflows
- **🚀 NEW: Webhook-driven Analysis**: Real-time code quality checks on push/PR
- **🚀 NEW: Email Reports**: Automated notifications to commit authors

## 🤖 LLM Integration (NEW!)

The framework now includes a **Model Context Protocol (MCP) server** that enables LLMs (Claude, GPT) to automatically analyze GitHub commits:

### Automated Workflow
```
GitHub Push → Webhook → LLM Analysis → Static Analysis Tools → Email Report
```

### Key Capabilities
- **Real-time commit analysis** triggered by GitHub webhooks
- **LLM-powered explanations** of code violations  
- **Automated email reports** to commit authors
- **Baseline comparisons** to track code quality trends
- **Multi-repository support** with access controls

### Quick Setup
```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with your GitHub token, LLM API key, and email settings

# 2. Start MCP server
./setup.sh

# 3. Configure GitHub webhook
# Repository → Settings → Webhooks → Add webhook
# URL: http://your-server:5000/webhook
```

See [`mcp_server/README.md`](mcp_server/README.md) for detailed setup and usage.

## Standards Compliance

- ✅ MISRA C:2012 (selected rules implemented)
- ✅ CERT C/C++ (selected rules implemented)
- ✅ ISO 26262 compatible output format
- ✅ ASPICE audit trail support

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Basic Usage

```bash
# Analyze C/C++ source code
python -m static_analyzer.cli --path src --standard MISRA --output report.json

# With AI explanations (optional)
python -m static_analyzer.cli --path src --standard MISRA --ai-explain --output report.json

# Custom deviation file
python -m static_analyzer.cli --path src --deviations deviations.yaml --output report.json
```

### Configuration

Create a `static_analyzer_config.yaml`:

```yaml
standards:
  - MISRA
  - CERT
  
rules:
  enabled:
    - MISRA-C-2012-8.7
    - MISRA-C-2012-10.1
    - CERT-EXP34-C
    
output:
  format: json
  include_source_context: true
  
ai_assistant:
  enabled: false
  model: "gpt-4"
```

## Architecture

```
static_analyzer/
├── ast/           # Clang AST layer
├── rules/         # Rule implementations
├── models/        # Data models
├── ai_assistant/  # AI explanation layer
├── config/        # Configuration management
└── cli.py         # Command-line interface
```

## Rule Implementation

The framework implements these rules out of the box:

- **MISRA-C-2012-8.7**: Objects should be defined at block scope
- **MISRA-C-2012-10.1**: Operands shall not be of inappropriate essential type
- **CERT-EXP34-C**: Do not dereference null pointers

## CI/CD Integration

Include the provided GitHub Actions workflow to automatically analyze pull requests:

```yaml
name: Static Analysis
on: [push, pull_request]
jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Static Analysis
        run: python -m static_analyzer.cli --path src --fail-on-new
```

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black .

# Type checking
mypy static_analyzer/
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## Safety Notice

This tool is designed for automotive and safety-critical applications. Always validate results through manual code review and domain expertise.
