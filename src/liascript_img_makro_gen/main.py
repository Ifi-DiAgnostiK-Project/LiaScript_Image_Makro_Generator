#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
minimal runner for keyword_extraction module
"""

import argparse
from liascript_img_makro_gen.generate_makros import LiaScriptMakroGenerator
from liascript_img_makro_gen.confighandler import ConfigLoader

def main():
    parser = argparse.ArgumentParser(
        description="Run the keyword extraction script with a custom config file location."
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to the configuration file.",
        default="config.yaml"
    )
    
    # Parse the command line arguments
    args = parser.parse_args()
    
    # Load the configuration and generate the makros using the provided config file
    loader = ConfigLoader(args.config)
    config = loader.load_config()
    LiaScriptMakroGenerator(config)

if __name__ == "__main__":
    main()