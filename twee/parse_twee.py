import re
import argparse

PASSAGE_LINE = re.compile('^:: *([^\[]*?) *(\[(.*?)\])? *(<(.*?)>)? *$')

class Passage(object):
    def __init__(self, name, tags=None, geometry=None, content=None):
        self.name = name
        self.tags = tags
        self.geometry = geometry
        if content is None:
            content = []
        self.content = content

    def __repr__(self):
        representation = 'Passage(' + self.name
        if self.tags is not None:
            representation += ', tags=' + repr(self.tags)
        if self.geometry is not None:
            representation += ', geometry=' + repr(self.geometry)
        representation += ')'

        return representation

    def __str__(self):
        return '\n'.join((self.passage_line, self.combined_content))

    @property
    def passage_line(self):
        passage_line = '::' + self.name
        if self.tags is not None:
            passage_line += ' [' + ' '.join(self.tags) + ']'
        if self.geometry is not None:
            passage_line += ' <' + ','.join(self.geometry) + '>'
        return passage_line

    @property
    def combined_content(self):
        return '\n'.join(self.content)

# Twee File Parsing

def parse_passage_line(line):
    """Parses a string defining a passage into data.

    Arguments:
        line: a string containing the line defining a new passage.

    Returns:
        passage_name: the name of the passage, as a string, or None if the line
        does not actually define a passage.
        tags: a list of non-empty string tags, or None if no tags were given.
        geometry: a tuple of geometry strings, or None if no geometry was given.
    """
    match = PASSAGE_LINE.match(line)
    if match is None:
        return (None, None, None)
    passage_name = match.group(1)
    try:
        tags = match.group(3).split(' ')
        tags = [tag for tag in tags if len(tag) > 0]
    except AttributeError:
        tags = None
    try:
        geometry = tuple(value for value in match.group(5).split(','))
    except AttributeError:
        geometry = None
    return (passage_name, tags, geometry)

def parse_lines(file_lines):
    """Parses a list of string lines into a dict of passages keyed by their names.

    Arguments:
        file_lines: a list of the lines of the file. Lines should have their newline
        \n characters stripped already.

    Returns:
        A dict of passages, where the key of each passage is its name
        and the value of each passage is a Passage object.
    """
    passages = {}
    current_passage = None
    for line in file_lines:
        if PASSAGE_LINE.match(line) is not None:
            if current_passage is not None:
                passages[current_passage.name] = current_passage
                print(str(current_passage))
            current_passage = Passage(*parse_passage_line(line))
        else:
            if current_passage is None:
                print('Warning: ignored line outside of passages: ' + line)
            else:
                current_passage.content.append(line)
    if current_passage is not None:
        passages[current_passage.name] = current_passage
        print(str(current_passage))

    return passages

def load_file(file_path):
    """Loads the file at the specified path as a list of strings.

    Returns:
        A list of strings, each holding one line. Lines have their \n newline
        characterss stripped already.
    """
    with open(file_path) as f:
        lines = [line.rstrip('\n') for line in f]
    return lines

def process_file(file_path):
    lines = load_file(file_path)
    passages = parse_lines(lines)
    return passages


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Split a monolithic Twee file into a structured Twee project.')
    parser.add_argument('file_path', type=str, help='Path of the input file to process.')
    args = parser.parse_args()
    process_file(args.file_path)
