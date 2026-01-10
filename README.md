# 🚀 ChromiumRunner

<div align="center">

**A tool for launching Chromium-based browsers with dynamic GUI and custom command-line arguments**

[![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
<!-- [![Platform](https://img.shields.io/badge/Platform-Windows-blue)](https://github.com/SavenkovIgor/ChromiumRunner) -->

</div>

## What it does

Launch Chromium-based browsers with specific flags and arguments — no need to type long command lines every time.

Under the hood, it uses a JSON configuration file that defines the browser path and arguments and generates a GUI with checkboxes, text inputs, and other controls.

### Features

- ✅ Enable/disable browser flags with checkboxes
- 📝 Support for flags, strings, numbers, and list arguments
- 💾 Settings are saved in JSON config files
- 🔧 Support for environment variables (`${env:VAR}`) and timestamps (`${tool:timestamp}`)
- 👁️ Preview the full command before running it

![ChromiumRunner Screenshot](resources/app.png)

### Setup & Running

With source code:

```bash
# Clone the repository
git clone https://github.com/SavenkovIgor/ChromiumRunner.git
cd ChromiumRunner

# Run the application directly:
./main.py

# Or using UV:
uv run main.py
```

## ⚙️ Configuration

Configuration files are JSON files in the application directory.

### Config File Example

```json
{
  "browser_path": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  "args": [
    {
        "name": "enable-logging",
        "description": "Enable logging",
        "type": "flag",
        "value": null,
        "enabled": true
    },
    {
      "name": "log-file",
      "description": "Path to the log file",
      "type": "string",
      "value": "${env:HOME}\\Desktop\\Chromium_${tool:timestamp}.log",
      "enabled": true
    }
  ]
}
```

### Argument Types

| Type | Description | Example |
| ---- | ----------- | ------- |
| `flag` | Simple boolean flag | `--disable-web-security` |
| `string` | Text value | `--user-data-dir="/path/to/profile"` |
| `number` | Numeric value | `--window-size=1920` |
| `list` | Comma-separated values | `--enable-features="WebGPU,Feature2"` |

### Value Interpolation

Supported dynamic values:

- **Environment variables**: `${env:VARIABLE_NAME}`
- **Timestamp**: `${tool:timestamp}` (format: `YYYY-MM-DD_HH-MM-SS`)
- **Escaping**: Use `\${...}` for literal text

**Example:**

```json
{
  "name": "user-data-dir",
  "type": "string",
  "value": "${env:TEMP}\\chrome-${tool:timestamp}"
}
```

## 🛠️ Tech stack

- Python 3.14
- [UV](https://github.com/astral-sh/uv) for dependency management and running the app
- [FreeSimpleGUI](https://github.com/spyoungtech/FreeSimpleGUI) for the UI
- PyInstaller for bundling into an executable

## 📦 Building

```bash
./build.py
```

Build output: `dist/ChromiumRunner.exe`
