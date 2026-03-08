from asyncio.log import logger
import json
import logging
from typing import Dict

from src.settings import FIXTURES_DIR

logger = logging.getLogger(__name__)


def read_from_json() -> Dict:
    file_path = f"{FIXTURES_DIR}/inventory.json"
    inventory_data = {}
    try:
        with open(file_path, "r") as fobj:
            inventory_data = json.load(fobj)
    except FileNotFoundError:
        logger.error("File %s does not exist", file_path)
    return inventory_data


def parse_inventory_json() -> Dict:
    inventory_data = read_from_json()
    return inventory_data


def prepare_package_version(version_string: str) -> str:
    version = ""
    return version
