from pathlib import Path
from unicodedata import category

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
        "how_to_use": "use images at {raw_location}",
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

def test_recursive_image_processing_with_images(image_tree, monkeypatch):
    monkeypatch.chdir(image_tree.parent)

    # Minimal config required by the constructor
    config = {
        "raw_image_folder": "https://raw.githubusercontent.com/user/repo/refs/heads/main/img",
        "ignore_dirs": ["ignore_folder"],
        "makros_setup": "",
        "makro_file": "makro.md",
        "image_folder": "img",  # Path inside which files are considered relative
        "how_to_use": "{raw_location}",
        "repository": "https://github.com/user/repo",
        "image_extensions": [".png", ".jpg", ".jpeg"],
    }

    gen = LiaScriptMakroGenerator(config)

    gen.process_folders()

    # join the body entries for easier assertions
    body = "\n".join(gen.makro_file._body)

    assert "@category1.one" in body, "image one is not correctly set"
    assert "@category1.two" in body, "image two is not correctly set"
    assert "@category2.three" in body, "image three is not correctly set"
    assert "@category2.four" in body, "image four is not correctly set"
    assert "@category1_subcategory.five" in body, "image five is not correctly set"
    assert "@category1_subcategory.six" in body, "image six is not correctly set"

def test_recursive_images_for_order(image_tree, monkeypatch):
    monkeypatch.chdir(image_tree.parent)

    # Minimal config required by the constructor
    config = {
        "raw_image_folder": "https://raw.githubusercontent.com/user/repo/refs/heads/main/img",
        "ignore_dirs": ["ignore_folder"],
        "makros_setup": "",
        "makro_file": "makro.md",
        "image_folder": "img",  # Path inside which files are considered relative
        "how_to_use": "{raw_location}",
        "repository": "https://github.com/user/repo",
        "image_extensions": [".png", ".jpg", ".jpeg"],
    }

    output_part = "|@category1.one(10)|_one_|`@category1.one(10)`|\n|@category1.two(10)|_two_|`@category1.two(10)`|"

    gen = LiaScriptMakroGenerator(config)

    gen.process_folders()

    # join the body entries for easier assertions
    body = "\n".join(gen.makro_file._body)

    assert output_part in body, "image order is not correct"

@pytest.fixture
def minimal_config():
    # adjust to match constructor requirements if needed
    return {
        "raw_image_folder": "raw",
        "ignore_dirs": [],
        "makros_setup": "",
        "makro_file": "makro.md",
        "image_folder": "img",
        "how_to_use": "",
        "repository": "",
        "image_extensions": (".png", ".jpg", ".jpeg"),
    }


def write_license_file(root: Path, name: str, content: str) -> Path:
    p = root / name
    p.write_text(content, encoding="utf-8")
    return p


def test_process_license_file_inserts_header_and_body_between_heading_and_table(tmp_path, minimal_config):
    """
    Given a repo location that contains a license file, process_licence_file should:
    - add a license-related macro/text to makro_file._header, and
    - insert the license text into makro_file._body between a Heading and the Start-of-Table marker.
    """
    repo = tmp_path / "repo"
    repo.mkdir()

    license_text = "Copyright (c) Example Org\nAll rights reserved."
    write_license_file(repo, "LICENSE", license_text)

    gen = LiaScriptMakroGenerator(minimal_config)

    heading = "# Images"
    table_start_marker = "<!-- START OF TABLE -->"
    gen.makro_file._body = [heading]


    # Call the method under test
    gen.process_license_file(repo, "repo")

    gen.makro_file.add_to_body(table_start_marker)

    # Header should contain some reference to the license (first line should appear or similar)
    header_text = "\n".join(gen.makro_file._header)
    assert header_text, "Expected makro_file._header to be non-empty after processing licence file"
    assert license_text.splitlines()[0] in header_text or "LICENSE" in header_text or "License" in header_text

    # Body should still contain the heading and the table start marker
    assert heading in gen.makro_file._body
    assert table_start_marker in gen.makro_file._body

    # License text (or its first line) must appear somewhere between heading and table_start_marker
    idx_heading = gen.makro_file._body.index(heading)
    idx_table = gen.makro_file._body.index(table_start_marker)

    assert idx_heading < idx_table, "Heading should be before the table start marker in the body"

    # Check that at least one body element between heading and table marker contains the license first line
    between = gen.makro_file._body[idx_heading + 1 : idx_table]
    assert between, "Expected content to be inserted between heading and table marker"
    assert any(license_text.splitlines()[0] in (str(item)) for item in between), (
        "Expected license text (or its first line) to be inserted between heading and table start marker"
    )


def test_process_license_file_no_license_file_leaves_header_and_body_unchanged(tmp_path, minimal_config):
    """
    If there is no license file in the provided location, process_licence_file should not raise
    and should not modify header/body (i.e. behave as a no-op).
    """
    repo = tmp_path / "repo_empty"
    repo.mkdir()

    gen = LiaScriptMakroGenerator(minimal_config)

    # snapshot initial header/body
    initial_header = list(gen.makro_file._header)
    initial_body = list(gen.makro_file._body)

    # Should not raise
    gen.process_license_file(repo, "repo_empty")

    assert gen.makro_file._header == initial_header, "Header changed even though no licence file was present"
    assert gen.makro_file._body == initial_body, "Body changed even though no licence file was present"

def test_process_license_file_two_levels_deep_macro_name(tmp_path, minimal_config):
    """
    If a LICENSE file is located two levels below the image folder (e.g. img/painter/tools/LICENSE),
    the generated macro name in the header should be composed from the folder names after the image
    folder joined with an underscore and suffixed with '.license', prefixed by '@'.
    Example: img->painter->tools->LICENSE  ->  @painter_tools.license
    """
    repo = tmp_path / "repo"
    tools_dir = repo / "img" / "painter" / "tools"
    tools_dir.mkdir(parents=True)

    license_text = "Copyright (c) Example Org\nAll rights reserved."
    # write_license_file is defined elsewhere in this test module
    write_license_file(tools_dir, "LICENSE", license_text)

    gen = LiaScriptMakroGenerator(minimal_config)

    # Ensure deterministic starting state
    gen.makro_file._header = []
    gen.makro_file._body = []

    # Execute
    gen.process_license_file(tools_dir, "painter_tools")

    header_text = "\n".join(gen.makro_file._header)
    assert "@painter_tools.license" in header_text, (
        "Expected macro '@painter_tools.license' to be present in header for a LICENSE file at img/painter/tools/LICENSE"
    )
