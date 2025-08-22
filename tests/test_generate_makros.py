import pytest
from liascript_img_makro_gen.generate_makros import LiaScriptMakroGenerator
from liascript_img_makro_gen.confighandler import ConfigLoader
from liascript_img_makro_gen.tools import DocumentBuilder


def test_constructor_sets_config_values():
    # Prepare a sample configuration with all required keys.
    config = {
        "raw_image_folder": "https://raw.githubusercontent.com/user/repo/refs/heads/main/img",
        "ignore_dirs": ["Collections"],
        "makros_setup": "<!--\nrepository: \"https://github.com/user/repo\"",
        "makro_file": "/makro.md",
        "image_folder": "/img",
        "how_to_use": "Some description text.",
        "image_extensions": [".jpg", ".jpeg", ".png", ".gif"],
        "repository": "https://github.com/user/repo",
    }

    # Instantiate the generator
    generator = LiaScriptMakroGenerator(config)

    # Verify that each member variable is set correctly.
    assert isinstance(generator.makro_file, DocumentBuilder), "makro_file not set correctly."
    assert generator.raw_image_folder == config["raw_image_folder"], "raw_image_folder not set correctly."
    assert generator.ignore_dirs == config["ignore_dirs"], "ignore_dirs not set correctly."
    assert generator.makros_setup == config["makros_setup"], "makros_setup not set correctly."
    assert generator.makro_filename == config["makro_file"], "makro_file not set correctly."
    assert generator.image_folder == config["image_folder"], "image_folder not set correctly."
    assert generator.how_to_use == config["how_to_use"], "how_to_use not set correctly."
    assert generator.image_extensions == config["image_extensions"], "image_extensions not set correctly."
    assert generator.repository == config["repository"], "repository not set correctly."

def test_generate_makros(monkeypatch):
    # Arrange: predictable location and no-op heavy methods on the generator class
    monkeypatch.setattr(ConfigLoader, "generate_raw_location", lambda repo, makro_file: "dummy_location")
    monkeypatch.setattr(
        LiaScriptMakroGenerator,
        "process_folders",
        lambda self: setattr(self, "process_folders_called", True),
    )
    monkeypatch.setattr(
        LiaScriptMakroGenerator,
        "save_makro_file",
        lambda self: setattr(self, "save_called", True),
    )

    config = {
        "raw_image_folder": "raw",
        "ignore_dirs": [],
        "makros_setup": "<!-- setup -->",
        "makro_file": "/not/used.md",
        "image_folder": "img",
        "how_to_use": "use images at {location}",
        "repository": "owner/repo",
        "image_extensions": [".jpg", ".png"],
    }

    # Act
    gen = LiaScriptMakroGenerator(config)
    # Ensure the generator uses the real DocumentBuilder for assertions
    gen.makro_file = DocumentBuilder()
    gen.generate_makros()

    # Assert: helpers were invoked and DocumentBuilder received expected content
    assert getattr(gen, "process_folders_called", False), "process_folders should have been called"
    assert getattr(gen, "save_called", False), "save_makro_file should have been called"

    result = gen.makro_file.build()

    assert "<!-- setup -->" in result
    assert "use images at dummy_location" in result