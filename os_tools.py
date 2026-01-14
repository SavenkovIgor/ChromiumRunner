import logging
import shutil
import subprocess
from pathlib import Path
from platform import system


class OsTools:
    @staticmethod
    def open_path(path: Path) -> None:
        """Open a file or directory using the system's default application."""
        if not path.exists():
            logging.error(f'Path does not exist: {path}')
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
            logging.error(f'Path does not exist: {path}')
            return
        try:
            if path.is_file():
                path.unlink()
                logging.info(f'Deleted file: {path}')
            elif path.is_dir():
                shutil.rmtree(path)
                logging.info(f'Deleted directory: {path}')
        except Exception as e:
            logging.error(f'Error deleting path {path}: {e}')
