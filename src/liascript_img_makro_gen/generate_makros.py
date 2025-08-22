import os
from pathlib import Path

from liascript_img_makro_gen.tools import DocumentBuilder
from liascript_img_makro_gen.confighandler import ConfigLoader

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
        img_path = os.path.join(os.getcwd(), self.image_folder)

        for entry in os.listdir(img_path):
            full_path = os.path.join(img_path, entry)

            if os.path.isdir(full_path) and entry not in self.ignore_dirs:
                # new folder, start with title and table
                self.makro_file.add_to_body(f"\n### {entry}\n\n|Bild|Name|Befehl|\n|---|---|---|")
                process_file(full_path)
