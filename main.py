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
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Self

from FreeSimpleGUI import (
    WIN_CLOSED,
    Button,
    Checkbox,
    Element,
    FileBrowse,
    HorizontalSeparator,
    Input,
    Text,
    Window,
    theme
)

window: Window | None = None  # Global window variable
theme("dark grey 9")

# Types
class Type:
    FLAG = "flag"
    STRING = "string"
    NUMBER = "number"
    LIST = "list"


@dataclass
class ArgListItem:
    enabled: bool
    value: str


@dataclass
class Arg:
    description: str
    enabled: bool
    arg: str
    type: Type
    value: str | int | list[ArgListItem] | None = None

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        """Create an Arg instance from a dictionary."""
        # Convert list items to ArgListItem instances if type is LIST
        if data.get("type") == Type.LIST:
            data = data.copy()
            data["value"] = [ArgListItem(**item) for item in data["value"]]
        return cls(**data)

    def __str__(self) -> str:
        if self.type == Type.STRING:
            assert self.value is not None
            return f"--{self.arg}=\"{self.value}\""

        if self.type == Type.FLAG:
            return f"--{self.arg}"

        if self.type == Type.NUMBER:
            assert self.value is not None
            return f"--{self.arg}={self.value}"

        if self.type == Type.LIST:
            assert isinstance(self.value, list)
            enabled_items = [item.value for item in self.value if item.enabled]
            joined_items = ",".join(enabled_items)
            return f"--{self.arg}={joined_items}"

        raise ValueError(f"Unknown Arg type: {self.type}")

    def create_checkbox(self) -> Checkbox:
        label = f"--{self.arg} ({self.description})"
        return Checkbox(
            key=f"{self.arg}_checkbox", text=label, default=self.enabled, enable_events=True
        )

    def create_spacer(self) -> Element:
        return Text("     ")

    def create_input(self) -> Input | None:
        key = f"{self.arg}_input"
        text = str(self.value) if self.value is not None else ""
        if self.type == Type.FLAG:
            return None
        if self.type == Type.STRING:
            return Input(key=key, default_text=text, size=(40, 1), enable_events=True)
        if self.type == Type.NUMBER:
            return Input(key=key, default_text=text, size=(20, 1), enable_events=True)
        if self.type == Type.LIST:
            return Input(key=key, default_text=text, size=(40, 1), enable_events=True)
        return None

    def create_layout_block(self) -> list[list[Element]]:
        ret: list[list[Element]] = []
        # Base checkbox to enable/disable the argument
        ret.append([self.create_checkbox()])

        if self.type == Type.LIST:
            assert isinstance(self.value, list)
            for item in self.value:
                ret.append(
                    [
                        self.create_spacer(),
                        Checkbox(text=f"{item.value}", default=item.enabled, enable_events=True),
                    ]
                )
            return ret

        input_field = self.create_input()
        if input_field is not None:
            ret.append([self.create_spacer(), input_field])
        return ret


class Config:
    def __init__(self, filepath: Path):
        json_data = json.loads(filepath.read_text())
        self.browser_path: Path = Path(json_data.get("browser_path", ""))
        self.args: list[Arg] = [Arg.from_dict(arg_data) for arg_data in json_data.get("args", [])]

    def enabled_args(self) -> list[str]:
        return [str(arg) for arg in self.args if arg.enabled]

    def run_command(self, decorate: bool = False) -> str:
        if decorate:
            args = self.enabled_args()
            args.insert(0, f'"{self.browser_path}"')
            return "\n".join(args)
        return f'"{self.browser_path}" {" ".join(self.enabled_args())}'


def read_all_configs() -> list[Config]:
    config_files = Path(__file__).parent.glob("*.config.json")
    ret = [Config(filepath) for filepath in config_files]
    ret = [ret[0]]  # Temporary: only load the first config
    return ret


def update_run_command_display(config: Config):
    global window
    if window is not None:
        window["run_command"].update(config.run_command(decorate=True))


def main():
    global window

    # Read configuration
    configs = read_all_configs()
    first_config = configs[0]
    print(f"Loaded {len(configs)} configuration")
    # Create a simple window with a "Hello World" label
    layout: list[list[Element]] = []
    layout.append([Text("Chromium Runner")])
    layout.append([HorizontalSeparator()])

    # Browser path
    layout.append(
        [
            Text("Browser Path:"),
            Input(default_text=str(first_config.browser_path), size=(60, 1)),
            FileBrowse(),
        ]
    )

    # Arguments
    layout.append([HorizontalSeparator()])
    layout.append([Text("Command-line arguments:")])
    layout.extend([arg.create_layout_block() for arg in first_config.args])

    # Resulting command
    layout.append([HorizontalSeparator()])
    layout.append([Text("Run Command:")])
    layout.append([Text(first_config.run_command(decorate=True), key="run_command")])

    # Run button
    layout.append([HorizontalSeparator()])
    layout.append([Button("Run Browser")])

    window = Window("Chromium Runner", layout)

    checkbox_elements = [f"{arg.arg}_checkbox" for arg in first_config.args]
    input_elements = [f"{arg.arg}_input" for arg in first_config.args]

    # Event loop
    while True:
        event, values = window.read()
        # print(f"Event: {event}\nValues: {values}")

        if event == WIN_CLOSED:
            break

        if event == "Run Browser":
            command = first_config.run_command()
            print(f"Running browser: {command}")
            subprocess.Popen(command, shell=True)

        if event in checkbox_elements:
            # Update the corresponding Arg instance
            for arg in first_config.args:
                if f"{arg.arg}_checkbox" == event:
                    arg.enabled = values[event]
                    break

            update_run_command_display(first_config)

        if event in input_elements:
            for arg in first_config.args:
                if f"{arg.arg}_input" == event:
                    if arg.type == Type.STRING:
                        arg.value = values[event]
                    elif arg.type == Type.NUMBER:
                        try:
                            arg.value = int(values[event])
                        except ValueError:
                            arg.value = 0
                    elif arg.type == Type.LIST:
                        # For simplicity, assume comma-separated values
                        items = values[event].split(",")
                        arg.value = [
                            ArgListItem(enabled=True, value=item.strip()) for item in items
                        ]
                    break

            update_run_command_display(first_config)

    window.close()


if __name__ == "__main__":
    main()
