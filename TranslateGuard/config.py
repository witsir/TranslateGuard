import json
import logging.config
from pathlib import Path

ROOT_PATH: Path = Path(__file__).parent.parent
CONFIG_PATH: Path = ROOT_PATH / ".TranslateGuard"


class LogJsonVerboseFilter(logging.Filter):
    """
    Verbose logging for print whole json data.
    Valid if has this value extra={'verbose': True}.
    """

    def filter(self, record):
        if hasattr(record, 'verbose') and record.verbose:
            return True
        return False


with open(CONFIG_PATH / "logging_config.json") as json_file:
    logging.config.dictConfig(json.load(json_file))
logging.getLogger("urllib3").setLevel(logging.WARNING)


def _get_user_agent_ua_local() -> dict | None:
    """
    Parse User-Agent, Sec-ch-ua, Version_main from local user_agent_ua.in
    """
    p = CONFIG_PATH / "user_agent_ua.in"
    if not p.exists():
        p.touch()
        return None
    else:
        with open(p, 'r') as f:
            return {"version_main": int(f.readline().strip()),
                    "User-Agent": f.readline().strip(),
                    "Sec-Ch-Ua": f.readline().strip()}


class Config:
    __slots__ = (
        "config",
        "USER_AGENT_UA",
        "ACCOUNTS",
        "API_KEYS",
        "PROXIES",
        "DEBUG",
        "DRIVER_EXECUTABLE_PATH",
        "PORT",
        "PATTERN_SPLIT",
        "SYSTEM_PROMPT",
        "USER_PROMPT_ADD",
        "SHOULD_DEL_CON",
        "FORCE_USING_CHAT_WEB_NUM"
    )

    def __init__(self, config_file_path):
        self.config = self.load_config(config_file_path)
        self.config["USER_AGENT_UA"] = _get_user_agent_ua_local()

    @staticmethod
    def load_config(config_file_path):
        with open(config_file_path, 'r') as f:
            return json.load(f)

    def __getattr__(self, name):
        return self.config[name]

    def __getitem__(self, key):
        return self.config[key]


config = Config(CONFIG_PATH / 'config.json')
