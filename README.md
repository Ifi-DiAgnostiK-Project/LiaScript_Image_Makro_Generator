# LiaScript_Image_Makro_Generator
[![Python CI](https://github.com/Ifi-DiAgnostiK-Project/LiaScript_Image_Makro_Generator/actions/workflows/ci.yml/badge.svg)](https://github.com/Ifi-DiAgnostiK-Project/LiaScript_Image_Makro_Generator/actions/workflows/ci.yml)

A Python Module that generates liascript makro files that link to image repos.

## Installation

Install via poetry after pulling the repo

```bash 
poetry install
```
then call the script via

```bash
poetry run python -m liascript_image_makro_generator.main --config config.yaml
```

## Configuration

The script is configured via a yaml file. An example config file is given in `config.yaml`.

