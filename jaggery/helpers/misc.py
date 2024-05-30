import os
import json

from typing import Literal
from datetime import datetime
from django.utils import timezone

from .exceptions import CaneException


def get_local_time() -> datetime:
    return timezone.now().astimezone(timezone.get_current_timezone())


class FileHandler:
    def read(file_path: str) -> str:
        if not os.path.exists(file_path):
            raise CaneException("File path does not exist")

        with open(file_path, "r") as file:
            return json.loads(file.read())

    def write(file_path: str, data: dict, mode: Literal["w", "a"] = "w") -> bool:
        directory = os.path.dirname(file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)

        with open(file_path, mode) as file:
            json.dump(data, file)

        return True


def get_local_isotime(value):
    return value.astimezone(timezone.get_current_timezone()).isoformat()
