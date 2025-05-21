# AutoData

**⚠️ The source code is currently being cleaned up and reorganized. Expect rapid changes and possible instability.**

Automatic web data collection via a multi-agent system with LLMs.

## Features

- 🤖 Modular multi-agent architecture
- 🧠 LLM-powered prompt-driven workflows
- 🔄 Automated, extensible data collection
- 📊 Structured data output
- 📝 Logging and error handling

## Installation

Activate your conda environment, then install dependencies:

```bash
conda activate autodata
pip install -e .
```

## Project Structure

```
AutoData/
├── agents/         # (Empty) Place agent implementations here
├── prompts/        # Markdown prompt templates and prompt loader utility
├── utils/          # Logging and utility functions
├── config.py       # Configuration management
├── exceptions.py   # Custom exceptions
├── __init__.py     # Package entry point
├── __version__.py  # Version info
├── py.typed        # PEP 561 type marker
tests/
├── test_logging.py # Example test
docs/               # (Empty) Documentation
examples/           # (Empty) Usage examples
assets/             # (Empty) Project assets
pyproject.toml      # Project configuration and dependencies
README.md           # Project overview and instructions
```

## Usage

> **Note:** The main agent and orchestration logic are under development.  
> To add your own agents, implement them in `AutoData/agents/`.  
> Prompt templates for LLMs are in `AutoData/prompts/`.

## Development

1. Clone the repository
2. Activate your conda environment:
   ```bash
   conda activate autodata
   ```
3. Install dependencies:
   ```bash
   pip install -e .
   ```
4. Run tests:
   ```bash
   pytest
   ```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.


