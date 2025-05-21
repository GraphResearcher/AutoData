# AutoData

Automatic web data collection via multi-agent system with LLMs.

## Features

- 🤖 Multi-agent system for distributed data collection
- 🧠 LLM-powered content understanding and extraction
- 🔄 Automated workflow management
- 📊 Structured data output
- 🔒 Robust error handling and retry mechanisms
- 📝 Comprehensive logging and monitoring

## Installation

```bash
# Using Rye (recommended)
rye sync

# Using pip
pip install autodata
```

## Quick Start

```python
from AutoData import AutoDataCollector

# Initialize the collector
collector = AutoDataCollector(
    llm_api_key="your-api-key",
    max_agents=3
)

# Start data collection
results = collector.collect(
    urls=["https://example.com"],
    extraction_rules={
        "title": "//h1",
        "content": "//article"
    }
)
```

## Project Structure

```
autodata/
├── src/
│   └── autodata/
│       ├── agents/         # Agent implementations
│       ├── core/           # Core functionality
│       ├── extractors/     # Data extraction modules
│       ├── llm/           # LLM integration
│       └── utils/         # Utility functions
├── tests/                 # Test suite
├── docs/                  # Documentation
└── examples/             # Usage examples
```

## Development

1. Clone the repository
2. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```
3. Run tests:
   ```bash
   pytest
   ```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


