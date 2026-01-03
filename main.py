#!/usr/bin/env -S uv run --script

import argparse
import json
import subprocess
import sys
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Self

from FreeSimpleGUI import (WIN_CLOSED, Button, Checkbox, Element, FileBrowse,
                           HorizontalSeparator, Input, Text, Window, theme)

# Set a theme for the GUI
theme("dark grey 9")


class Os:
    @staticmethod
    def is_win() -> bool:
        return sys.platform.startswith("win")

    @staticmethod
    def is_lin() -> bool:
        return sys.platform.startswith("linux")


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
        if Os.is_win():
            return 1.5

        if Os.is_lin():
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
            pass


# Types
class ArgType:
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
    def from_dict(cls, data: dict) -> Self:
        """Create an Arg instance from a dictionary."""
        # Convert list items to ArgListItem instances if type is LIST
        if data.get("type") == ArgType.LIST:
            data = data.copy()
            data["value"] = [ArgListItem(**item) for item in data["value"]]
        return cls(**data)

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
        json_data = json.loads(filepath.read_text())

        browser_path_dict = json_data.get("browser_path", {})
        if browser_path_dict:
            if Os.is_win():
                self.browser_path: Path = Path(browser_path_dict.get("win", ""))
            elif Os.is_lin():
                self.browser_path: Path = Path(browser_path_dict.get("lin", ""))
        else:
            assert False, "browser_path must be specified in config"

        self.args: list[Arg] = [Arg.from_dict(arg_data) for arg_data in json_data.get("args", [])]

    def run_browser_command(self) -> list[str]:
        args: list[str] = [str(self.browser_path)]
        # Add enabled arguments
        args.extend([str(arg) for arg in self.args if arg.enabled])
        return args

    def decorated_run_browser_command(self) -> str:
        return '\n'.join(self.run_browser_command())

    @classmethod
    def load_configs(cls, config_dir: Path) -> list[Self]:
        config_files: list[Path] = sorted(config_dir.glob(f"*.config.json"))
        return [cls(filepath) for filepath in config_files]


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
            return configs[0]

        print("No configuration files found. Exiting.")
        return None

    def _run_browser(self) -> None:
        command = self.config.run_browser_command()
        print(f'Running browser: {" ".join(command)}')
        subprocess.Popen(command, shell=True)

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
        label = f"{arg.flag_name} ({arg.description})"
        return Checkbox(key=key, text=label, default=arg.enabled, enable_events=True)

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
        ret.append([App.create_arg_checkbox(arg)])

        if arg.type == ArgType.LIST:
            assert isinstance(arg.value, list)
            for item in arg.value:
                ret.append(
                    [
                        App.h_spacer(),
                        Checkbox(text=f"{item.value}", default=item.enabled, enable_events=True),
                    ]
                )
            return ret

        input_field = App.create_arg_input(arg)
        if input_field is not None:
            ret.append([App.h_spacer(), input_field])
        return ret

    def _create_main_window(self) -> Window:
        assert self.config is not None, "Config must be loaded before creating the window"
        layout: list[list[Element]] = []
        layout.append([Text("Chromium Runner")])
        layout.append([HorizontalSeparator()])

        # Browser path
        bp_row: list[Element] = []
        bp_row.append(Text("Browser Path:"))
        bp_row.append(Input(default_text=str(self.config.browser_path), size=(60, 1)))
        bp_row.append(FileBrowse())
        layout.append(bp_row)

        # Arguments
        layout.append([HorizontalSeparator()])
        layout.append([Text("Command-line arguments:")])
        for arg in self.config.args:
            layout.extend(self._create_layout_for_arg(arg))

        # Resulting command
        layout.append([HorizontalSeparator()])
        layout.append([Text("Run Command:")])
        layout.append([self.command_output])

        # Run button
        layout.append([HorizontalSeparator()])
        key = 'run_browser_button'
        layout.append([Button("Run Browser", key=key)])
        self.handlers[key] = self._run_browser

        return Window("Chromium Runner", layout)

    def run_event_loop(self) -> None:
        checkbox_elements = [f"{arg.name}_checkbox" for arg in self.config.args]
        input_elements = [f"{arg.name}_input" for arg in self.config.args]

        # Event loop
        while True:
            event, values = self.window.read()
            # print(f"Event: {event}\nValues: {values}")

            if event == WIN_CLOSED:
                break

            if event in self.handlers:
                self.handlers[event]()
                continue

            if event in checkbox_elements:
                # Update the corresponding Arg instance
                for arg in self.config.args:
                    if f"{arg.name}_checkbox" == event:
                        arg.enabled = values[event]
                        break

                self._update_run_command_display()

            if event in input_elements:
                for arg in self.config.args:
                    if f"{arg.name}_input" == event:
                        if arg.type == ArgType.STRING:
                            arg.value = values[event]
                        elif arg.type == ArgType.NUMBER:
                            try:
                                arg.value = int(values[event])
                            except ValueError:
                                arg.value = 0
                        elif arg.type == ArgType.LIST:
                            # For simplicity, assume comma-separated values
                            items = values[event].split(",")
                            arg.value = [
                                ArgListItem(enabled=True, value=item.strip()) for item in items
                            ]
                        break

                self._update_run_command_display()

        self.window.close()


def main(args: argparse.Namespace) -> None:
    App().run_event_loop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    args = parser.parse_args()

    UiContext.init_app_scaling()

    main(args)
