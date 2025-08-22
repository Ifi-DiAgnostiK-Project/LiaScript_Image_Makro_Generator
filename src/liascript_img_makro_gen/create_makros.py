import os
from pathlib import Path

from src.liascript_img_makro_gen.tools import get_sanitized_name, is_image_file

ignore_dirs = ['Collections']

makros_setup = '''<!--
author: Volker Göhler, Niklas Werner
email: volker.goehler@informatik.tu-freiberg
version: 0.0.4
repository: https://github.com/Ifi-DiAgnostiK-Project/Bildersammlung
edit: true
title: DiAgnostiK Bilder Makros

tags: Wissensspeicher

@diagnostik_url_pics: https://raw.githubusercontent.com/Ifi-DiAgnostiK-Project/Bildersammlung/refs/heads/main/img

@diagnostik_image_pics: <img src="@0/@1" alt="@1" style="height: @2rem">
'''

location = 'https://raw.githubusercontent.com/Ifi-DiAgnostiK-Project/Bildersammlung/refs/heads/main/makros.md'

how_to_use = f'''
# Link zu LiaScript

[![LiaScript Course](https://raw.githubusercontent.com/LiaScript/LiaScript/master/badges/course.svg)](https://liascript.github.io/course/?{location})


> Diese Datei ist automatisch generiert und enthält Makros für die DiAgnostiK-Bilder der Gewerke.

# Anleitung

> Der Befehl zum einbinden eines Bildes lautet `@<Bereich>.<Name>(Größe)`.
> Hängt man statt der Größe `.src` an den Befehl an, so wird der Link zum Bild angezeigt. `@<Bereich>.<Name>.src`
> - Der Bereich ist der Ordnername, in dem sich das Bild befindet.
> - Der Name ist der Dateiname ohne Endung.
> - Die Größe ist in Zeilen angegeben, die das Bild hoch sein soll.
Alle Bilder sowie ihre Bereiche und die Befehle um sie zu laden sind in den Tabellen weiter unten abgebildet.
**Die Anzeige benötigt LiaScript!**

## Beispiel

`@Maler_Taetigkeiten.Koje_Grundflaeche_farbig(10)`

@Maler_Taetigkeiten.Koje_Grundflaeche_farbig(10)

@Maler_Taetigkeiten.Koje_Grundflaeche_farbig.src

`@Maler_Taetigkeiten.Koje_Grundflaeche_farbig.src`

## Bereiche und Befehle

Im Nachfolgenden sind alle Bilder aller Bereiche und passende Befehle aufgelistet, die in dieser Sammlung enthalten sind.
'''


def process_folders(base_path):
    img_path = os.path.join(base_path, 'img')
    makros = [makros_setup]
    showcase = [how_to_use]

    for entry in os.listdir(img_path):
        full_path = os.path.join(img_path, entry)

        if os.path.isdir(full_path) and entry not in ignore_dirs:
            showcase.append(f"\n### {entry}\n\n|Bild|Name|Befehl|\n|---|---|---|")
            process_file(full_path, makros, showcase)

    makros.append("\n-->\n")

    return "\n".join(makros) + "\n".join(showcase)

def clean_filename(filename):
    itemname = Path(filename).stem
    return itemname.replace('_', ' ').replace('-', ' ')

def process_file(parent_folder, makros, showcase):
    """This writes a makro and a showcase for all files in a given folder."""
    for item in os.listdir(parent_folder):
        full_path = os.path.join(parent_folder, item)
        if os.path.isdir(full_path):
            process_file(full_path, makros, showcase)
        if os.path.isfile(full_path) and is_image_file(item, image_extensions=?):
            # Only process image files
            filename = get_sanitized_name(item)
            entries = Path(parent_folder).parts[-2:]
            entry = "_".join(entries)
            parent_folders = Path(*entries).as_posix()
            makros.append("")
            makros.append(f'@{entry}.{filename}.src: @diagnostik_url_pics/{parent_folders}/{item}')
            makros.append(f'@{entry}.{filename}: @diagnostik_image_pics(@diagnostik_url_pics,{parent_folders}/{item},@0)')

            itemname = clean_filename(item)
            showcase.append(f"|@{entry}.{filename}(10)|_{itemname}_|`@{entry}.{filename}(10)`|")


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    text = process_folders(current_dir)
    makros_path = os.path.join(current_dir, "makros.md")
    with open(makros_path, "w", encoding="utf-8") as f:
        f.write(text)
