import logging
import sys
from pathlib import Path

import yaml

class ConfigLoader:
    def __init__(self, config_path="config.yaml"):
        """
        Initialisiert den ConfigLoader und lädt die Konfiguration.

        :param config_path: Pfad zur Konfigurationsdatei.
        """
        self.config_path = config_path

    def load_config(self):
        """
        Loads the configuration file and sets default values for missing keys.

        :return: A dictionary containing the configuration.
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                config_data = yaml.safe_load(file) or {}
        except FileNotFoundError:
            logging.error(f"Configuration file not found: {self.config_path}")
            sys.exit(1)
        except yaml.YAMLError as e:
            logging.error(f"Error reading configuration file: {e}")
            sys.exit(1)

        # Default values for keys missing in the configuration file
        defaults = {
            "ignore_dirs": [],
            "makros_setup": "",
            "makro_file": "makros.md",
            "image_folder": "img",
            "how_to_use": "",
            "image_extensions": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"]
        }

        # Set default values for keys that are not present
        for key, default_value in defaults.items():
            config_data.setdefault(key, default_value)

        config_data = ConfigLoader.__ensure_validity(config_data)
        config_data = ConfigLoader.__process_makros_setup(config_data)
        config_data["raw_image_folder"] = self.generate_raw_location(config_data["repository"], config_data["image_folder"])
        return config_data

    @staticmethod
    def __ensure_validity(config_data: dict) -> dict:
        # Ensure the 'repository' key is provided; raise an exception if not.
        if not config_data.get("repository"):
            raise ValueError("The 'repository' key must be provided in the configuration.")

        # Strip leading slashes from  'makro_file' and 'image_folder'
        keys = ["makro_file", "image_folder"]
        for key in keys:
            path_key = Path(config_data[key])
            if path_key.root != '':
                config_data[key] = path_key.relative_to("/")

        # ensure that all image_extensions are lowercase
        config_data["image_extensions"] = ["." + e.lower() if not e.startswith('.') else e.lower() for e in config_data["image_extensions"]]

        return config_data

    @staticmethod
    def __process_makros_setup(config_data: dict) -> dict:
        # Process the 'makros_setup' key
        makros_setup = config_data.get("makros_setup")
        # Split the content into lines.
        lines = makros_setup.splitlines()
        # Remove leading empty lines.
        while lines and lines[0].strip() == "":
            lines.pop(0)
        # Ensure the first non-empty line starts with the HTML comment tag.
        if not lines or not lines[0].strip().startswith("<!--"):
            lines.insert(0, "<!--")
        # Replace or add the repository line with the repository key from the configuration.
        repo_line_found = False
        updated_lines = []
        for line in lines:
            stripped_line = line.lstrip()
            if stripped_line.startswith("repository:"):
                updated_lines.append(f'repository: "{config_data["repository"]}"')
                repo_line_found = True
            else:
                updated_lines.append(line)
        if not repo_line_found:
            # Insert the repository line right after the comment tag.
            if len(updated_lines) > 1:
                updated_lines.insert(1, f'repository: "{config_data["repository"]}"')
            else:
                updated_lines.append(f'repository: "{config_data["repository"]}"')
        config_data["makros_setup"] = "\n".join(updated_lines)
        return config_data

    @staticmethod
    def generate_raw_location(repository_url: str, makro_file: str) -> str:
        """
        Converts a GitHub repository URL (e.g. https://github.com/user/reponame/)
        into its corresponding raw URL for the makro file.

        :param repository_url: The GitHub repository URL.
        :param makro_file: The path to the makro file (default is "/makros.md").
        :return: The raw URL suitable to access the file.
        """
        # Remove any trailing slashes from the repository URL.
        repository_url = repository_url.rstrip("/")

        # Split the URL to extract the path after 'github.com/'
        try:
            repo_path = repository_url.split("github.com/")[1]
        except IndexError:
            raise ValueError("The provided repository URL is invalid. It must contain 'github.com/'")

        # Construct the raw URL.
        # Here we assume 'refs/heads/main' is the default branch.
        raw_url = f"https://raw.githubusercontent.com/{repo_path}/refs/heads/main/{makro_file}"
        return raw_url