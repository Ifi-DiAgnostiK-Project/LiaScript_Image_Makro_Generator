from pathlib import Path

import pytest
from liascript_img_makro_gen.generate_makros import LiaScriptMakroGenerator
from liascript_img_makro_gen.confighandler import ConfigLoader
from liascript_img_makro_gen.tools import DocumentBuilder


@pytest.fixture
def image_tree(tmp_path):
    """
    Create a temporary folder structure:
    tmp_path/
      img/
        category1/
          subcategory/
            five.png
            six.png
          ignore_folder/
          one.png
          two.jpg
        category2/
          three.png
          four.jpeg
        ignore_folder/
    Returns the Path to the img directory.
    """
    img = tmp_path / "img"
    cat1 = img / "category1"
    cat2 = img / "category2"
    cat3 = cat1 / "subcategory"
    cat4 = img / "ignore_folder"
    cat5 = cat1 / "ignore_folder"
    cat1.mkdir(parents=True)
    cat2.mkdir(parents=True)
    cat3.mkdir(parents=True)
    cat4.mkdir()
    cat5.mkdir()

    # create minimal image files (content doesn't matter for the test)
    (cat1 / "one.png").write_bytes(b"\x89PNG\r\n")
    (cat1 / "two.jpg").write_bytes(b"\xFF\xD8\xFF")
    (cat2 / "three.png").write_bytes(b"\x89PNG\r\n")
    (cat2 / "four.jpeg").write_bytes(b"\xFF\xD8\xFF")
    (cat3 / "five.png").write_bytes(b"\x89PNG\r\n")
    (cat3 / "six.png").write_bytes(b"\x89PNG\r\n")

    return img


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
    gen.generate_makros()

    # Assert: helpers were invoked and DocumentBuilder received expected content
    assert getattr(gen, "process_folders_called", False), "process_folders should have been called"
    assert getattr(gen, "save_called", False), "save_makro_file should have been called"

    result = gen.makro_file.build()

    assert "<!-- setup -->" in result
    assert "use images at dummy_location" in result

def test_process_file():
    """
    An image file should generate a src and an image macro and table text for the same image.
    :return:
    """
    config = {
        "raw_image_folder": "https://raw.githubusercontent.com/owner/repo/refs/heads/main/img",
        "ignore_dirs": [],
        "makros_setup": "<!-- setup ",
        "makro_file": "/makro.md",
        "image_folder": "img",
        "how_to_use": "use images at {location}",
        "repository": "https://github.com/owner/repo",
        "image_extensions": [".jpg", ".png"],
    }
    gen = LiaScriptMakroGenerator(config)
    gen.process_file(Path("category/test-one.jpg"))

    head = '@category.test_one.src: https://raw.githubusercontent.com/owner/repo/refs/heads/main/img/category/test-one.jpg\n' + \
    '@category.test_one: @diagnostik_image(https://raw.githubusercontent.com/owner/repo/refs/heads/main/img,category/test-one.jpg,@0)'
    body = "|@category.test_one(10)|_test one_|`@category.test_one(10)`|"

    result = gen.makro_file.build()

    assert head == result.split('-->')[0].strip(), "Head macros don't have correct format"
    assert body == result.split('-->')[1].strip(), "Body output does not has correct format"

def test_process_file_raises_value_error_when_path_is_relative_to_image_folder():
    # Minimal config required by the constructor
    config = {
        "raw_image_folder": "raw",
        "ignore_dirs": [],
        "makros_setup": "",
        "makro_file": "makro.md",
        "image_folder": "/img",
        "how_to_use": "",
        "repository": "",
        "image_extensions": [".png", ".jpg"],
    }

    gen = LiaScriptMakroGenerator(config)

    # A path that is inside the configured image_folder should raise the ValueError
    with pytest.raises(ValueError, match="Image path should not be relative to image_folder"):
        gen.process_file(Path("/img/picture.png"))

def test_recursive_image_processing(image_tree, monkeypatch):
    monkeypatch.setattr(
        LiaScriptMakroGenerator,
        "process_file",
        lambda self, _: setattr(self, "process_file_called", getattr(self, "process_file_called", 0) + 1),
    )
    monkeypatch.chdir(image_tree.parent)

    # Minimal config required by the constructor
    config = {
        "raw_image_folder": "raw",
        "ignore_dirs": ["ignore_folder"],
        "makros_setup": "",
        "makro_file": "makro.md",
        "image_folder": "img",  # Path inside which files are considered relative
        "how_to_use": "",
        "repository": "",
        "image_extensions": [".png", ".jpg"],
    }

    gen = LiaScriptMakroGenerator(config)

    gen.process_folders()

    # join the body entries for easier assertions
    body = "\n".join(gen.makro_file._body)

    # process_folders adds a section header for each category
    assert "### category1" in body, "Category Entry for 1 is missing in the body"
    assert "### category2" in body, "Category Entry for 2 is missing in the body"
    assert "### category1_subcategory" in body, "Category Entry for cat1/subcat is missing in the body"

    assert body.count("|Bild|Name|Befehl|") == 3, "There should be three table heads in the body"

    assert gen.process_file_called == 5, "process_file should have been called for each image file"

def test_recursive_image_processing_no_ignores(image_tree, monkeypatch):
    monkeypatch.setattr(
        LiaScriptMakroGenerator,
        "process_file",
        lambda self, _: setattr(self, "process_file_called", getattr(self, "process_file_called", 0) + 1),
    )
    monkeypatch.chdir(image_tree.parent)

    # Minimal config required by the constructor
    config = {
        "raw_image_folder": "raw",
        "ignore_dirs": [],
        "makros_setup": "",
        "makro_file": "makro.md",
        "image_folder": "img",  # Path inside which files are considered relative
        "how_to_use": "",
        "repository": "",
        "image_extensions": [".png", ".jpg", ".jpeg"],
    }

    gen = LiaScriptMakroGenerator(config)

    gen.process_folders()

    # join the body entries for easier assertions
    body = "\n".join(gen.makro_file._body)

    # process_folders adds a section header for each category
    assert "### category1" in body, "Category Entry for 1 is missing in the body"
    assert "### category2" in body, "Category Entry for 2 is missing in the body"
    assert "### ignore_folder" in body, "Ignore Folder in top directory is missing in the body"
    assert "### category1_subcategory" in body, "Category Entry for cat1/subcat is missing in the body"
    assert "### category1_ignore_folder" in body, "Category Entry for cat1/ignore_folder is missing in the body"

    assert body.count("|Bild|Name|Befehl|") == 5, "There should be three table heads in the body"

    assert gen.process_file_called == 6, "process_file should have been called for each image file"