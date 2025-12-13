#!/usr/bin/env -S uv run --script

# /// script
# name = "chromium-runner"
# version = "0.1.0"
# description = "Simple GUI for running Chromium-based browsers with custom command-line arguments"
# readme = "README.md"
# requires-python = ">=3.14"
# dependencies = ["freesimplegui>=5.2.0.post1"]
# ///

import FreeSimpleGUI as sg


def main():
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
