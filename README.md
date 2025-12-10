# ChromiumRunner

A Python-based GUI application that provides a convenient interface for running Chromium-based browsers with custom command-line arguments.

## Project Overview

ChromiumRunner is designed with simplicity in mind, offering a straightforward user experience for launching Chromium-based browsers (Chrome, Edge, Brave, etc.) with pre-configured command-line arguments.

### Key Features

- **Simple UX**: Minimal, intuitive interface for maximum ease of use
- **Command-Line Arguments**: Easily configure and save browser launch parameters
- **Multiple Browsers**: Support for various Chromium-based browsers
- **JSON Configuration**: All settings stored in a simple JSON format for easy editing and portability

## Technical Details

### Development

- **Language**: Python
- **Dependency Manager**: [UV](https://github.com/astral-sh/uv) - A fast Python package installer and resolver
- **Configuration Storage**: JSON format for easy manipulation and version control

### Distribution

The application is compiled into native executables for different platforms:

- **Windows**: `.exe` executable
- **macOS**: `.dmg` disk image
- **Linux**: `.AppImage` portable application

## Project Goals

The main goal of ChromiumRunner is to provide a convenient, cross-platform UI for launching Chromium-based browsers with specific command-line arguments, eliminating the need to remember or manually type complex command-line flags each time you want to start your browser with custom settings.
