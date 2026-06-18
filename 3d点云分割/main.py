# main.py
import asyncio
import yaml
from pathlib import Path


async def main():
    config_path = Path(__file__).parent / "config.yaml"
    config = yaml.safe_load(config_path.read_text())
    print("Loaded config:", config["browser"]["cdp_url"])
    # TODO: wire modules


if __name__ == "__main__":
    asyncio.run(main())
