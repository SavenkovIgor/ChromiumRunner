#!/usr/bin/env -S uv run --script

import subprocess

subprocess.run(['pyinstaller', 'ChromiumRunner.spec', '--clean'], check=True)
