import os
import re
from pathlib import Path
from typing import Tuple, Any


def replace_umlaut(match):
            char = match.group(0)
            return UMLAUT_MAP.get(char, char)


UMLAUT_MAP = {
    'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue', 'ß': 'ss'
}


def get_sanitized_name(filepath):
    """
    Extracts the name from a given file path by normalizing special characters and ensuring
    it contains only valid alphanumeric characters or underscores. Replaces umlauts or other
    special characters based on a predefined mapping and substitutes invalid characters with
    underscores.

    :param filepath: The file path from which the name is extracted.
    :type filepath: str
    :return: A normalized string derived from the file name, with invalid characters replaced
        by underscores.
    :rtype: str
    """
    filename = os.path.splitext(os.path.basename(filepath))[0]
    pattern = '[' + ''.join(map(re.escape, UMLAUT_MAP.keys())) + ']'
    filename = re.sub(pattern, replace_umlaut, filename)
    return re.sub(r'\W', '_', filename, flags=re.ASCII)


def is_image_file(filename, image_extensions):
    """Check if the file is an image based on its extension."""
    extension = Path(filename).suffix.lower()
    return extension in image_extensions


class DocumentBuilder:
    def __init__(self):
        self._header = []
        self._body = []

    def add_to_header(self, content: str):
        self._header.append(content)

    def add_to_body(self, content: str):
        self._body.append(content)

    def build(self) -> str:
        return "\n".join(self._header) + "\n-->\n\n" + "\n".join(self._body)


def clean_filename(filename):
    """
    Return the filename but underscores and dashes are replaced with spaces.
    :param filename:
    :return:
    """
    itemname = Path(filename).stem
    return itemname.replace('_', ' ').replace('-', ' ')
