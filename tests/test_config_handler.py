from pathlib import Path

import pytest
from liascript_img_makro_gen.confighandler import ConfigLoader
import yaml

from src.liascript_img_makro_gen.confighandler import ConfigLoader

# Since __ensure_validity is a private method, we need to get it via name mangling.
ensure_validity = ConfigLoader._ConfigLoader__ensure_validity
process_makros_setup = ConfigLoader._ConfigLoader__process_makros_setup


def test_img_folder_leading_slash_removed():
    config_data = {
        "repository": "https://github.com/user/reponame",
        "image_folder": "/img",
        "makro_file": "/makro.md",
        "image_extensions": []
    }
    updated = ensure_validity(config_data)
    assert Path(updated["image_folder"]).root == '', "image_folder should not start with a leading slash"

def test_img_folder_moved_to_full_variable(tmp_path):
    # Create a temporary config.yaml file with only the mandatory repository key.
    config = {
        "repository": "https://github.com/user/repo"
    }
    config_file = tmp_path / "config.yaml"
    with open(config_file, "w", encoding="utf-8") as f:
        yaml.dump(config, f)

    # Instantiate the ConfigLoader with the temporary config file.
    loader = ConfigLoader(config_path=str(config_file))
    config_data = loader.load_config()
    assert "image_folder" in config_data, "image_folder should be present in the config data"
    assert config_data["image_folder"] == "img", "image_folder should be set to 'img'"
    assert config_data["raw_image_folder"] == "https://raw.githubusercontent.com/user/repo/refs/heads/main/img", "raw_image_folder should be set to the raw URL"

def test_missing_repository_raises_error():
    config_data = {
        "makros_setup": "some setup",
        "makro_file": "makro.md"
    }
    with pytest.raises(ValueError, match="The 'repository' key must be provided"):
        ensure_validity(config_data)

def test_makro_file_leading_slash_striped():
    config_data = {
        "repository": "https://github.com/user/reponame",
        "makros_setup": "some setup",
        "makro_file": "/makro.md",
        "image_folder": "/img",
        "image_extensions": []
    }
    updated = ensure_validity(config_data)
    assert not Path(updated["makro_file"]).root, "makro_file should not start with a leading slash"

def test_makros_setup_adds_html_comment_and_repository_line_when_missing():
    # Start with some empty lines, then a normal text not starting with the comment and no repository line.
    config_data = {
        "repository": "https://github.com/user/reponame",
        "makros_setup": "\n\n  author: Test Author\n  some: value"
    }
    updated = process_makros_setup(config_data)
    lines = updated["makros_setup"].splitlines()
    # Check that the first non-empty line starts with the HTML comment tag.
    assert lines[0].startswith("<!--"), "First line must be an HTML comment tag"
    # Check that the repository key is inserted on the second line.
    assert lines[1] == 'repository: "https://github.com/user/reponame"', "Repository line must be added after the comment"

def test_makros_setup_replaces_existing_repository_line():
    # makros_setup already contains a repository line that should be replaced.
    original_makros = """<!--
author: Test Author
repository: "https://github.com/old/repo"
edit: true
"""
    config_data = {
        "repository": "https://github.com/user/newrepo",
        "makros_setup": original_makros
    }
    updated = process_makros_setup(config_data)
    lines = updated["makros_setup"].splitlines()
    # Find the repository line
    repo_lines = [line for line in lines if line.lstrip().startswith("repository:")]
    assert repo_lines, "There should be a repository line after ensuring validity."
    assert repo_lines[0] == 'repository: "https://github.com/user/newrepo"', "Repository line should be updated to the new repository value."

def test_generate_raw_location():
    # Test the conversion of a GitHub repository URL to a raw URL.
    repository_url = "https://github.com/user/reponame/"
    makro_file = "makros.md"
    expected_raw = "https://raw.githubusercontent.com/user/reponame/refs/heads/main/makros.md"
    raw_url = ConfigLoader.generate_raw_location(repository_url, makro_file)
    assert raw_url == expected_raw, f"Expected {expected_raw}, got {raw_url}"

def test_defaults_are_set(tmp_path):
    # Create a temporary config.yaml file with only the mandatory repository key.
    config = {
        "repository": "https://github.com/user/repo"
    }
    config_file = tmp_path / "config.yaml"
    with open(config_file, "w", encoding="utf-8") as f:
        yaml.dump(config, f)

    # Instantiate the ConfigLoader with the temporary config file.
    loader = ConfigLoader(config_path=str(config_file))
    config_data = loader.load_config()

    # Define the expected defaults.
    expected_defaults = {
        "ignore_dirs": [],
        "makros_setup": '<!--\nrepository: "https://github.com/user/repo"',
        "makro_file": "makros.md",
        "image_folder": "img",
        "how_to_use": "",
        "image_extensions": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"]
    }

    # Check that each default key is present and holds the expected value.
    # For 'makros_setup', we check that it starts with the HTML comment and repository line.
    assert config_data["ignore_dirs"] == expected_defaults["ignore_dirs"], "Default ignore_dirs not set correctly."
    assert config_data["makro_file"] == expected_defaults["makro_file"], "Default makro_file not set correctly."
    assert config_data["image_folder"] == expected_defaults["image_folder"], "Default image_folder not set correctly."
    assert config_data["how_to_use"] == expected_defaults["how_to_use"], "Default how_to_use not set correctly."
    assert config_data["image_extensions"] == expected_defaults["image_extensions"], "Default image_extensions not set correctly."
    assert config_data["repository"] == "https://github.com/user/repo", "Repository value not preserved correctly."

    # For makros_setup, check that it starts with the HTML comment tag and has the repository line.
    makros_lines = config_data["makros_setup"].splitlines()
    assert makros_lines[0].startswith("<!--"), "makros_setup should start with an HTML comment tag."
    # Check that one of the lines is the repository line.
    repo_line = 'repository: "https://github.com/user/repo"'
    assert any(line.strip() == repo_line for line in makros_lines), "Repository line not correctly added in makros_setup."

def test_image_extensions_lowercased():
    config_data = {
        "repository": "https://github.com/user/reponame",
        "image_folder": "/img",
        "makros_setup": "<!--\nrepository: \"https://github.com/user/reponame\"",
        "makro_file": "/makro.md",
        "image_extensions": [".JPG", ".PNG"]
    }
    updated = ensure_validity(config_data)
    assert updated["image_extensions"] == [".jpg", ".png"], "Image extensions should be lowercased."

def test_image_extensions_start_with_dot():
    config_data = {
        "repository": "https://github.com/user/reponame",
        "image_folder": "/img",
        "makros_setup": "<!--\nrepository: \"https://github.com/user/reponame\"",
        "makro_file": "/makro.md",
        "image_extensions": ["jpg", ".png", "jpeg"]
    }
    updated = ensure_validity(config_data)
    assert updated["image_extensions"] == [".jpg", ".png", ".jpeg"], "Image extensions should start with a dot."
