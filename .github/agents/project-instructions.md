# ChromiumRunner - Custom Agent Instructions

## Project Type

This is a **Python project** that creates a desktop GUI application.

## Dependency Management

The project uses **UV** as its dependency manager. UV is a fast Python package installer and resolver from Astral.

### Working with Dependencies

- Use `uv` commands for managing dependencies (e.g., `uv add <package>`, `uv remove <package>`)
- Dependencies are managed through UV's configuration files
- Do not use pip, poetry, or other dependency managers

## Build and Distribution

The Python application is compiled into native executables for distribution:

### Target Platforms and Formats

1. **Windows**: `.exe` executable file
2. **macOS**: `.dmg` disk image
3. **Linux**: `.AppImage` portable application

### Build Process

The application needs to be packaged into standalone executables using appropriate tools (e.g., PyInstaller, cx_Freeze, or similar) for each target platform.

## Project Purpose

ChromiumRunner provides a **convenient graphical user interface** for running Chromium-based browsers with custom command-line arguments.

### Core Functionality

- Launch Chromium-based browsers (Chrome, Edge, Brave, etc.)
- Configure and save browser command-line arguments
- Simple, intuitive user interface
- Cross-platform support

## Configuration Storage

All application configuration is stored in **JSON format**.

### Configuration Details

- Config file(s) use JSON structure
- Settings include browser paths and command-line arguments
- JSON format allows for easy editing and version control

## UX Guidelines

The application prioritizes **simplicity and ease of use**:

- Minimal interface with clear, straightforward controls
- Quick access to common tasks
- No unnecessary complexity
- Focus on efficiency and user convenience

## Development Guidelines

When working on this project:

1. Maintain the simple, focused UX approach
2. Use UV for all dependency management tasks
3. Ensure cross-platform compatibility
4. Keep JSON configuration format simple and readable
5. Test that the application can be successfully compiled to exe/dmg/AppImage
6. Follow Python best practices and conventions
