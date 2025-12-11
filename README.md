# ChromiumRunner

Simple GUI for running Chromium-based browsers with custom command-line arguments.

## Tech Stack

- **Language**: Python
- **GUI Library**: [FreeSimpleGUI](https://github.com/spyoungtech/FreeSimpleGUI) (fork of PySimpleGUI)
- **Dependency Manager**: [UV](https://github.com/astral-sh/uv)
- **Config**: JSON
- **Builds**: `.exe` (Windows), `.dmg` (macOS), `.AppImage` (Linux)

## Installation

1. Install UV (if not already installed):
```bash
pip install uv
```

2. Install dependencies:
```bash
uv sync
```

## Running the Application

Run the application using UV:
```bash
uv run python main.py
```

Or activate the virtual environment and run directly:
```bash
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
python main.py
```

## Requirements

- Python 3.12 or higher
- tkinter (usually comes with Python, but on Linux you may need to install `python3-tk`)
