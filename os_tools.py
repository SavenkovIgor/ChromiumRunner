import shutil
import subprocess
from pathlib import Path
from platform import system


class OsTools:
    @staticmethod
    def open_path(path: Path) -> None:
        """Open a file or directory using the system's default application."""
        if not path.exists():
            print(f'Path does not exist: {path}')
            return
        cmd: dict = {
            'Windows': 'explorer',
            'Darwin': 'open',
            'Linux': 'xdg-open',
        }
        opener = cmd.get(system(), '')
        subprocess.Popen([opener, str(path)])

    @staticmethod
    def delete_path(path: Path) -> None:
        """Delete a file or directory at the given path."""
        if not path.exists():
            print(f'Path does not exist: {path}')
            return
        try:
            if path.is_file():
                path.unlink()
                print(f'Deleted file: {path}')
            elif path.is_dir():
                shutil.rmtree(path)
                print(f'Deleted directory: {path}')
        except Exception as e:
            print(f'Error deleting path {path}: {e}')
