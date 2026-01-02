#!/usr/bin/env -S uv run --script

import argparse
import json
import subprocess
import sys
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from typing import Self

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
    description: str
    enabled: bool
    arg: str
    type: ArgType
    value: str | int | list[ArgListItem] | None = None

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        """Create an Arg instance from a dictionary."""
        # Convert list items to ArgListItem instances if type is LIST
        if data.get("type") == ArgType.LIST:
            data = data.copy()
            data["value"] = [ArgListItem(**item) for item in data["value"]]
        return cls(**data)

    def __str__(self) -> str:
        if self.type == ArgType.STRING:
            assert self.value is not None
            return f"--{self.arg}=\"{self.value}\""

        if self.type == ArgType.FLAG:
            return f"--{self.arg}"

        if self.type == ArgType.NUMBER:
            assert self.value is not None
            return f"--{self.arg}={self.value}"

        if self.type == ArgType.LIST:
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
        if self.type == ArgType.FLAG:
            return None
        if self.type == ArgType.STRING:
            return Input(key=key, default_text=text, size=(40, 1), enable_events=True)
        if self.type == ArgType.NUMBER:
            return Input(key=key, default_text=text, size=(20, 1), enable_events=True)
        if self.type == ArgType.LIST:
            return Input(key=key, default_text=text, size=(40, 1), enable_events=True)
        return None

    def create_layout_block(self) -> list[list[Element]]:
        ret: list[list[Element]] = []
        # Base checkbox to enable/disable the argument
        ret.append([self.create_checkbox()])

        if self.type == ArgType.LIST:
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

    def enabled_args(self) -> list[str]:
        return [str(arg) for arg in self.args if arg.enabled]

    def run_browser_command(self, decorate: bool = False) -> str:
        if decorate:
            args = self.enabled_args()
            args.insert(0, f'"{self.browser_path}"')
            return "\n".join(args)
        return f'"{self.browser_path}" {" ".join(self.enabled_args())}'

    @classmethod
    def load_configs(cls, config_dir: Path) -> list[Self]:
        config_files: list[Path] = sorted(config_dir.glob(f"*.config.json"))
        return [cls(filepath) for filepath in config_files]


class App:
    # Main app window and config
    window: Window | None = None
    config: Config | None = None

    def load_first_config(self) -> bool:
        config_dir = AppContext.config_dir()
        configs = Config.load_configs(config_dir)
        if configs:
            self.config = configs[0]
            print(f"Loaded configuration: {self.config.path}")
            return True

        print("No configuration files found. Exiting.")
        return False

    def update_run_command_display(self) -> None:
        if self.window is not None and self.config is not None:
            cmd = self.config.run_browser_command(decorate=True)
            self.window["run_browser_command"].update(cmd)

    def create_window(self) -> None:
        layout: list[list[Element]] = []
        layout.append([Text("Chromium Runner")])
        layout.append([HorizontalSeparator()])

        # Browser path
        layout.append(
            [
                Text("Browser Path:"),
                Input(default_text=str(self.config.browser_path), size=(60, 1)),
                FileBrowse(),
            ]
        )

        # Arguments
        layout.append([HorizontalSeparator()])
        layout.append([Text("Command-line arguments:")])
        layout.extend([arg.create_layout_block() for arg in self.config.args])

        # Resulting command
        layout.append([HorizontalSeparator()])
        layout.append([Text("Run Command:")])
        layout.append(
            [Text(self.config.run_browser_command(decorate=True), key="run_browser_command")]
        )

        # Run button
        layout.append([HorizontalSeparator()])
        layout.append([Button("Run Browser")])

        self.window = Window("Chromium Runner", layout)

    def run_event_loop(self) -> None:
        checkbox_elements = [f"{arg.arg}_checkbox" for arg in self.config.args]
        input_elements = [f"{arg.arg}_input" for arg in self.config.args]

        # Event loop
        while True:
            event, values = self.window.read()
            # print(f"Event: {event}\nValues: {values}")

            if event == WIN_CLOSED:
                break

            if event == "Run Browser":
                command = self.config.run_browser_command()
                print(f"Running browser: {command}")
                subprocess.Popen(command, shell=True)

            if event in checkbox_elements:
                # Update the corresponding Arg instance
                for arg in self.config.args:
                    if f"{arg.arg}_checkbox" == event:
                        arg.enabled = values[event]
                        break

                self.update_run_command_display()

            if event in input_elements:
                for arg in self.config.args:
                    if f"{arg.arg}_input" == event:
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

                self.update_run_command_display()

        self.window.close()


def main(args: argparse.Namespace) -> None:
    app = App()
    if not app.load_first_config():
        return

    app.create_window()
    app.run_event_loop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    args = parser.parse_args()

    UiContext.init_app_scaling()

    main(args)
