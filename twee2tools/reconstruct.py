#!/usr/bin/env python3

import argparse

import passages
import projects
from projects import populate_project_tree

# File Processing

def process_file(file_path, output_path):
    """Splits a monolithic Twee file into a structured Twee project."""
    tree = projects.populate_project_tree(passages.parse_file(file_path))
    tree.reconstruct(output_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Split a monolithic Twee file into a structured Twee project.')
    parser.add_argument('file_path', type=str, help='Path of the input file to process.')
    parser.add_argument('output_path', type=str,
                        help='Path of the root of the output directory tree to make.')
    args = parser.parse_args()
    process_file(args.file_path, args.output_path)
