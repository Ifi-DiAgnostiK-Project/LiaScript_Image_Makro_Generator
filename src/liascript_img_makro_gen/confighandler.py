import logging
import os
import sys

import yaml


def load_config(config_path="config.yaml"):
    """Lädt die Konfigurationsdatei."""
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        logging.error(f"Konfigurationsdatei nicht gefunden: {config_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        logging.error(f"Fehler beim Lesen der Konfigurationsdatei: {e}")
        sys.exit(1)

