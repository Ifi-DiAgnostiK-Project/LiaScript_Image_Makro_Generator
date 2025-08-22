import pytest
from src.liascript_img_makro_gen.tools import get_sanitized_name
from src.liascript_img_makro_gen.tools import is_image_file

@pytest.mark.parametrize("filepath, expected", [
    # Simple filename with umlauts only:
    ("./äöü.jpg", "aeoeue"),
    # Filename with umlaut ß and invalid characters:
    ("./straße.txt", "strasse"),
    # Filename with a mix of umlauts, apostrophes and hyphens:
    ("Bär's-image_123.png", "Baer_s_image_123"),
    # Already sanitized filename:
    ("./normal_file.txt", "normal_file"),
    # Filename with multiple invalid characters:
    ("./file@name$$.doc", "file_name__"),
    # Filename with digits and underscores:
    ("./123_file.png", "123_file"),
])
def test_get_sanitized_name(filepath, expected):
    # The function extracts the basename and removes the extension, so we only care about that part
    result = get_sanitized_name(filepath)
    assert result == expected, f"Expected '{expected}' for '{filepath}', but got '{result}'"


# Define a tuple of valid image extensions.
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp")

@pytest.mark.parametrize("filename,expected", [
    ("picture.jpg", True),
    ("photo.jpeg", True),
    ("graphic.png", True),
    ("animation.GIF", True),  # Mixed case should be handled by lower()
    ("scan.BMp", True),
    ("diagram.TIFF", True),
    ("icon.webp", True),
    ("document.pdf", False),
    ("archive.zip", False),
    ("script.py", False),
    ("image.jpgg", False),
    ("no_extension", False)
])
def test_is_image_file(filename, expected):
    result = is_image_file(filename, IMAGE_EXTENSIONS)
    assert result == expected, f"Expected {expected} for filename '{filename}', got {result}"
