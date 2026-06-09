import os
import sys
from dotenv import load_dotenv


def _get_app_dir() -> str:
    if getattr(sys, 'frozen', False):
        app_data = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        app_dir = os.path.join(app_data, "SentinelAI")
    else:
        app_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(app_dir, exist_ok=True)
    return app_dir


_env_path = os.path.join(_get_app_dir(), ".env")
load_dotenv(_env_path)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
