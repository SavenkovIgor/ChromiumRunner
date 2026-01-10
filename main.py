#!/usr/bin/env -S uv run --script

import argparse
import json as Json
import os
import re
import subprocess
import sys
import tkinter as tk
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Callable, Self

from FreeSimpleGUI import (WIN_CLOSED, Button, Checkbox, Element, Frame,
                           HorizontalSeparator, Input, Text, Window, theme)

# Set a theme for the GUI
theme("dark grey 8")


class AppContext:
    @staticmethod
    def script_dir() -> Path:
        """Get the dir where the script or binary is located.

        When frozen (PyInstaller), this returns the directory containing the executable.
        When running from source, it returns the directory containing this script.
        """
        script_dir: str = sys.executable if getattr(sys, "frozen", False) else sys.argv[0]
        return Path(script_dir).resolve().parent

    @staticmethod
    def config_dir() -> Path:
        return AppContext.script_dir()


class UiContext:
    @staticmethod
    def app_scaling() -> float:
        if sys.platform.startswith('win'):
            return 1.5

        if sys.platform.startswith('linux'):
            return 3.0

        return 1.0

    @staticmethod
    def init_app_scaling() -> None:
        # Init the tk scaling
        try:
            root = tk.Tk()
            root.withdraw()
            print(f"window info:")
            print(f"  pixels per inch: {root.winfo_fpixels('1i')}")
            print(f"  current scaling: {root.tk.call('tk', 'scaling')}")

            root.tk.call("tk", "scaling", UiContext.app_scaling())
        except Exception:
            print("Failed to set UI scaling")
            pass


class ValueInterpolator:
    """
    Simple interpolator for `${env:NAME}` and `${tool:timestamp}` patterns with escaping support.
    Supports the `env:` provider and `tool:timestamp` which returns the current time in ISO 8601 (UTC).
    """

    def timestamp(self) -> str:
        """Return current UTC timestamp in a filename-safe format (e.g. 2026-01-11_12-34-56)."""
        # Use UTC and produce a hyphenated filename-safe timestamp: YYYY-MM-DD_HH-MM-SS
        return datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")

    def interpolate_string(self, s: str) -> str:
        pattern = re.compile(r'(\\)?\$\{([^}]+)\}')

        def repl(m):
            ENV_PREFIX = "env:"
            TOOL_PREFIX = "tool:"
            # If escaped with backslash (group 1), return the literal without the backslash.
            if m.group(1):
                return "${" + m.group(2) + "}"

            inner = m.group(2)
            if inner.startswith(ENV_PREFIX):
                name = inner[len(ENV_PREFIX) :]
                val = os.environ.get(name)
                if val is not None:
                    return val
                else:
                    print(f"Missing env var: {name}")

            if inner.startswith(TOOL_PREFIX):
                name = inner[len(TOOL_PREFIX) :]
                if name == "timestamp":
                    return self.timestamp()

            # Unknown provider; leave placeholder unchanged.
            return f'${{{inner}}}'

        return pattern.sub(repl, s)


class ArgType(Enum):
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
    name: str
    description: str
    type: ArgType
    value: str | int | list[ArgListItem] | None = None
    enabled: bool = True

    @classmethod
    def from_json(cls, json: dict) -> Self:
        json = json.copy()
        json["type"] = ArgType(json["type"])
        if json["type"] == ArgType.LIST:
            json["value"] = [ArgListItem(**item) for item in json["value"]]
        return cls(**json)

    def to_json(self) -> dict:
        json: dict = {}
        json["name"] = self.name
        json["description"] = self.description
        json["type"] = self.type.value
        if self.type == ArgType.LIST and isinstance(self.value, list):
            json["value"] = [asdict(item) for item in self.value]
        else:
            json["value"] = self.value

        json["enabled"] = self.enabled
        return json

    @property
    def flag_name(self) -> str:
        return f"--{self.name}"

    def __str__(self) -> str:
        if self.type == ArgType.STRING:
            assert self.value is not None
            return f'{self.flag_name}="{self.value}"'

        if self.type == ArgType.FLAG:
            assert self.value is None
            return self.flag_name

        if self.type == ArgType.NUMBER:
            assert self.value is not None
            return f'{self.flag_name}={self.value}'

        if self.type == ArgType.LIST:
            assert isinstance(self.value, list)
            enabled_items = [item.value for item in self.value if item.enabled]
            joined_items = ','.join(enabled_items)
            return f'{self.flag_name}="{joined_items}"'

        raise ValueError(f"Unknown Arg type: {self.type}")


class Config:
    def __init__(self, filepath: Path):
        self.path: Path = filepath
        json = Json.loads(filepath.read_text())
        self.browser_path = Path(json.get("browser_path", ""))
        if not self.browser_path.exists():
            raise FileNotFoundError(f"No browser found at path: {self.browser_path}")

        self.args: list[Arg] = [Arg.from_json(arg_data) for arg_data in json.get("args", [])]

    def save(self) -> None:
        json: dict = {}
        json["browser_path"] = str(self.browser_path)
        json["args"] = [arg.to_json() for arg in self.args]
        self.path.write_text(Json.dumps(json, indent=4) + "\n", newline='\n')

    @classmethod
    def load_configs(cls, config_dir: Path) -> list[Self]:
        config_files: list[Path] = sorted(config_dir.glob(f"*.config.json"))
        return [cls(filepath) for filepath in config_files]

    def run_browser_command(self) -> list[str]:
        args: list[str] = [str(self.browser_path)]
        # Add enabled arguments
        interpolator = ValueInterpolator()
        for arg in self.args:
            if not arg.enabled:
                continue
            args.append(interpolator.interpolate_string(str(arg)))
        return args

    def decorated_run_browser_command(self) -> str:
        return '\n'.join(self.run_browser_command())

    def find_arg(self, arg_name: str) -> Arg | None:
        return next((arg for arg in self.args if arg.name == arg_name), None)

    def find_arg_list_item(self, arg_list_name: str) -> ArgListItem | None:
        for arg in self.args:
            if arg.type != ArgType.LIST:
                continue
            assert isinstance(arg.value, list)
            for item in arg.value:
                full_name = f"{arg.name}_{item.value}"
                if full_name == arg_list_name:
                    return item
        return None

    def set_value(self, arg_name: str, value: str) -> None:
        arg = self.find_arg(arg_name)
        assert arg is not None, f"Argument with name '{arg_name}' not found in config"
        if arg.type == ArgType.STRING:
            assert isinstance(value, str)
            arg.value = value
        elif arg.type == ArgType.NUMBER:
            try:
                arg.value = int(value)
            except ValueError:
                arg.value = 0
        elif arg.type == ArgType.LIST:
            # For simplicity, assume comma-separated values
            items = value.split(",")
            arg.value = [ArgListItem(enabled=True, value=item.strip()) for item in items]


class App:
    def __init__(self) -> None:
        first_config = self._load_first_config()
        assert first_config is not None, "Failed to load any configuration"
        self.config = first_config

        # UI elements
        self.handlers: dict[str, Callable] = {}
        self.command_output = Text(self.config.decorated_run_browser_command())
        self.window = self._create_main_window()

    def _load_first_config(self) -> Config | None:
        config_dir = AppContext.config_dir()
        configs = Config.load_configs(config_dir)
        if configs:
            print(f"Loaded configuration: {configs[0].path}")
            configs[0].save()  # Save to ensure any defaults are written
            return configs[0]

        print("No configuration files found. Exiting.")
        return None

    def _run_browser(self) -> None:
        command = self.config.run_browser_command()
        command_str = ' '.join(command)
        print(f'Running browser: {command_str}')
        subprocess.Popen(command_str)

    def _update_run_command_display(self) -> None:
        if self.window is not None and self.config is not None:
            cmd = self.config.decorated_run_browser_command()
            self.command_output.update(cmd)

    @staticmethod
    def h_spacer() -> Element:
        return Text("     ")

    @staticmethod
    def create_arg_checkbox(arg: Arg) -> Checkbox:
        key = f"{arg.name}_checkbox"
        return Checkbox(key=key, text=arg.flag_name, default=arg.enabled, enable_events=True)

    @staticmethod
    def create_arg_input(arg: Arg) -> Input | None:
        if arg.type not in (ArgType.STRING, ArgType.NUMBER):
            return None

        assert arg.value is not None
        key = f"{arg.name}_input"
        text = str(arg.value)
        return Input(key=key, default_text=text, size=(40, 1), enable_events=True)

    @staticmethod
    def _create_layout_for_arg(arg: Arg) -> list[list[Element]]:
        ret: list[list[Element]] = []
        # Base checkbox to enable/disable the argument
        row: list[Element] = []
        row.append(App.create_arg_checkbox(arg))
        ret.append(row)

        if arg.type == ArgType.LIST:
            assert isinstance(arg.value, list)
            for item in arg.value:
                key = f'{arg.name}_{item.value}_list_checkbox'
                text = f'{item.value}'
                item_row: list[Element] = []
                item_row.append(App.h_spacer())
                item_row.append(
                    Checkbox(key=key, text=text, default=item.enabled, enable_events=True)
                )
                ret.append(item_row)
        else:
            input_field = App.create_arg_input(arg)
            if input_field is not None:
                row.append(input_field)

        # Wrap everything in a frame
        return [[Frame(arg.description, ret, expand_x=True)]]

    def _create_main_window(self) -> Window:
        assert self.config is not None, "Config must be loaded before creating the window"
        layout: list[list[Element]] = []
        app_description = 'Run Chromium with custom arguments'
        layout.append([Text(app_description, font=("Any", 12))])
        layout.append([HorizontalSeparator()])

        # Browser path
        bp_row: list[Element] = []
        bp_row.append(Text("Browser Path:"))
        bp_row.append(Input(default_text=str(self.config.browser_path), size=(60, 1)))
        layout.append(bp_row)

        # Arguments
        layout.append([HorizontalSeparator()])
        layout.append([Text("Command-Line Arguments:")])
        for arg in self.config.args:
            layout.extend(self._create_layout_for_arg(arg))

        # Resulting command
        layout.append([HorizontalSeparator()])
        layout.append([Text("Result Command:")])
        layout.append([self.command_output])

        # Run button
        layout.append([HorizontalSeparator()])
        key = 'run_browser_button'
        layout.append([Button("Run Browser", key=key)])
        self.handlers[key] = self._run_browser

        return Window("Chromium Runner", layout)

    def run_event_loop(self) -> None:
        list_checkbox_suffix = "_list_checkbox"
        checkbox_suffix = "_checkbox"
        input_suffix = "_input"

        # Event loop
        while True:
            event, values = self.window.read()
            # print(f"Event: {event}\nValues: {values}")

            if event == WIN_CLOSED:
                break

            if event in self.handlers:
                self.handlers[event]()

            elif event.endswith(list_checkbox_suffix):
                arg_list_item_name = event.replace(list_checkbox_suffix, "", -1)
                item = self.config.find_arg_list_item(arg_list_item_name)
                if item is not None:
                    item.enabled = values[event]
                    self.config.save()

            elif event.endswith(checkbox_suffix):
                # Cut off the suffix to get the arg name
                arg_name = event.replace(checkbox_suffix, "", -1)
                arg = self.config.find_arg(arg_name)
                if arg is not None:
                    arg.enabled = values[event]
                    self.config.save()

            elif event.endswith(input_suffix):
                arg_name = event.replace(input_suffix, "", -1)
                self.config.set_value(arg_name, values[event])
                self.config.save()

            self._update_run_command_display()

        self.window.close()


def main(args: argparse.Namespace) -> None:
    UiContext.init_app_scaling()
    App().run_event_loop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    main(parser.parse_args())
