import platform

"""Default json configuration for ChromiumRunner. Will be written to disk if no config file exists."""

# If no config file exists, this default will be written to disk
DEFAULT_CONFIG_WINDOWS: dict = {
    "browser_path": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "additional_paths": [
        "${env:USERPROFILE}\\AppData\\Local\\Google\\Chrome\\User Data",
        "${env:USERPROFILE}\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Preferences",
    ],
    "args": [
        {
            "name": "user-data-dir",
            "description": "User data directory path",
            "type": "string",
            "value": "${env:USERPROFILE}\\Desktop\\User Data",
            "enabled": True,
        },
        {
            "name": "enable-logging",
            "description": "Enable logging",
            "type": "flag",
            "value": None,
            "enabled": True,
        },
        {
            "name": "log-file",
            "description": "Log file path",
            "type": "string",
            "value": "${env:USERPROFILE}\\Desktop\\Chromium_${tool:timestamp}.log",
            "enabled": True,
        },
        {
            "name": "vmodule",
            "description": "Modules log verbosity (module=level,...)",
            "type": "list",
            "value": [
                {"enabled": True, "value": "net=2"},
                {"enabled": False, "value": "gpu=1"},
                {"enabled": True, "value": "renderer=3"},
            ],
            "enabled": True,
        },
    ],
}

DEFAULT_CONFIG_LINUX: dict = {
    "browser_path": "/snap/bin/chromium",
    "additional_paths": [
        "${env:HOME}/.config/chromium",
        "${env:HOME}/.config/chromium/Default/Preferences",
    ],
    "args": [
        {
            "name": "user-data-dir",
            "description": "User data directory path",
            "type": "string",
            "value": "${env:HOME}/Desktop/User Data",
            "enabled": True,
        },
        {
            "name": "enable-logging",
            "description": "Enable logging",
            "type": "flag",
            "value": None,
            "enabled": True,
        },
        {
            "name": "log-file",
            "description": "Log file path",
            "type": "string",
            "value": "${env:HOME}/Desktop/Chromium_${tool:timestamp}.log",
            "enabled": True,
        },
        {
            "name": "vmodule",
            "description": "Modules log verbosity (module=level,...)",
            "type": "list",
            "value": [
                {"enabled": True, "value": "net=2"},
                {"enabled": False, "value": "gpu=1"},
                {"enabled": True, "value": "renderer=3"},
            ],
            "enabled": True,
        },
    ],
}

CONFIGS = {'Windows': DEFAULT_CONFIG_WINDOWS, 'Linux': DEFAULT_CONFIG_LINUX}

DEFAULT_CONFIG: dict = CONFIGS.get(platform.system(), DEFAULT_CONFIG_WINDOWS)
