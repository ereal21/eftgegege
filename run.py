import importlib
import subprocess
import sys

REQUIRED_MODULES = [
    "yoomoney",
    "aiogram",
    "sqlalchemy",
    "requests",
    "alembic",
    "solana",
    "xrpl",
    "web3",
    "bitcoinrpc",
]


def ensure_requirements() -> None:
    """Install required packages if any are missing."""
    missing = []
    for module in REQUIRED_MODULES:
        try:
            importlib.import_module(module)
        except Exception:
            missing.append(module)

    if missing:
        subprocess.check_call([
            sys.executable,
            "-m",
            "pip",
            "install",
            "-r",
            "requirements.txt",
        ])


from bot import start_bot

if __name__ == '__main__':
    ensure_requirements()
    start_bot()
