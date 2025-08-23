import os
from pathlib import Path

from liascript_img_makro_gen.confighandler import ConfigLoader
from liascript_img_makro_gen.tools import DocumentBuilder, is_image_file, get_sanitized_name, clean_filename


class LiaScriptMakroGenerator:
    def __init__(self, config: dict):
        self.makro_file = DocumentBuilder()
        self.raw_image_folder = config["raw_image_folder"]
        self.ignore_dirs = config["ignore_dirs"]
        self.makros_setup = config["makros_setup"]
        self.makro_filename = config["makro_file"]
        self.image_folder = config["image_folder"]
        self.how_to_use = config["how_to_use"]
        self.repository = config["repository"]
        self.image_extensions = config["image_extensions"]

    def generate_makros(self):
        # output pre fill
        self.makro_file.add_to_header(self.makros_setup)
        self.makro_file.add_to_body(self.how_to_use.format(location=ConfigLoader.generate_raw_location(self.repository, self.makro_file)))

        # parse all image folders
        self.process_folders()

        # generate document
        self.save_makro_file()

    def save_makro_file(self):
        makro_path = Path(os.getcwd()) / self.makro_filename
        with open(makro_path, "w", encoding="utf-8") as f:
            f.write(self.makro_file.build())

    def process_folders(self):
        img_path = Path(os.getcwd()) / Path(self.image_folder)

        self.process_folder(img_path)

    def process_folder(self, target: Path):
        """
        Recursive Method to write headers, execute file entries and step deeper into the subfolders.
        :param target: Path of the current folder.
        :return: None
        """
        operation_folder = target.name
        # parse only folders in the main image directory
        at_top = True if operation_folder == self.image_folder else False

        # we go through all entries in path
        for category in os.listdir(target):
            full_path = target / category
            # each of these main categories needs to be parsed for subcats and image files
            if os.path.isdir(full_path) and category not in self.ignore_dirs:
                # directory
                if not at_top:
                    # if we are not at top then add subcategory
                    category = f"{operation_folder}_{category}"
                # new folder, start with title and table
                self.makro_file.add_to_body(f"\n### {category}\n")
                self.makro_file.add_to_body("|Bild|Name|Befehl|\n|---|---|---|")
                self.process_folder(full_path)
            elif os.path.isfile(full_path) and is_image_file(category, image_extensions=self.image_extensions):
                # image
                self.process_file(full_path)

    def process_file(self, filepath: Path):
        """
        This generates the makros and explanation table entries for a single image file.
        :param filepath: only the path with the filename after image_folder
        :return:
        """
        # should not start with img
        if filepath.is_relative_to(self.image_folder):
            raise ValueError("Image path should not be relative to image_folder")

        # the name of the file with extension
        item = filepath.name
        # without extension and cleared from non ANSII's
        filename = get_sanitized_name(item)
        # we join the folders above filename with _
        parent_folders = Path(filepath).parts[:-1]
        categories = "_".join(parent_folders)
        parents_for_url = Path(*parent_folders).as_posix()

        self.makro_file.add_to_header("")
        self.makro_file.add_to_header(f'@{categories}.{filename}.src: {self.raw_image_folder}/{parents_for_url}/{item}')
        self.makro_file.add_to_header(f'@{categories}.{filename}: @diagnostik_image({self.raw_image_folder},{parents_for_url}/{item},@0)')

        item_name = clean_filename(item)
        self.makro_file.add_to_body(f"|@{categories}.{filename}(10)|_{item_name}_|`@{categories}.{filename}(10)`|")