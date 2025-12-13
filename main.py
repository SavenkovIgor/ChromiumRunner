#!/usr/bin/env -S uv run --script

# /// script
# name = "chromium-runner"
# version = "0.1.0"
# description = "Simple GUI for running Chromium-based browsers with custom command-line arguments"
# readme = "README.md"
# requires-python = ">=3.14"
# dependencies = ["freesimplegui>=5.2.0.post1"]
# ///

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Self

import FreeSimpleGUI as sg


# Types
class Type:
    FLAG = "flag"
    STRING = "string"


@dataclass
class Arg:
    ui_label: str
    ui_desc: str
    enabled: bool
    arg: str
    type: Type
    value: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        """Create an Arg instance from a dictionary."""
        return cls(**data)

    def __str__(self) -> str:
        if self.type == Type.STRING:
            assert self.value
            return f"{self.arg}=\"{self.value}\""

        if self.type == Type.FLAG:
            return self.arg


class Config:
    def __init__(self, filepath: Path):
        json_data = json.loads(filepath.read_text())
        self.browser_path: Path = Path(json_data.get("browser_path", ""))
        self.args: list[Arg] = [Arg.from_dict(arg_data) for arg_data in json_data.get("args", [])]


def read_all_configs() -> list[Config]:
    config_files = Path(__file__).parent.glob("*.config.json")
    return [Config(filepath) for filepath in config_files]


def main():
    # Read configuration
    configs = read_all_configs()
    print(f"Loaded {len(configs)} configuration(s).")
    print(configs)
    # Create a simple window with a "Hello World" label
    layout = [[sg.Text("Hello World")]]
    window = sg.Window("Hello World App", layout)

    # Event loop
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break

    window.close()


if __name__ == "__main__":
    main()
