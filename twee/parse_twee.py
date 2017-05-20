import collections
import re
import argparse

# The regex for parsing passage definition lines
PASSAGE_LINE = re.compile('^:: *([^\[]*?) *(\[(.*?)\])? *(<(.*?)>)? *$')

# Passage names and tags which will not end up in files
SPECIAL_PASSAGES = {'Start', 'StorySubtitle', 'StoryAuthor', 'StoryMenu',
                    'StorySettings', 'StoryIncludes'}
SPECIAL_TAGS = {'stylesheet', 'script', 'haml', 'twee2'}

# Passage names and tags of special project-level passages
PROJECT_PASSAGES = {'PassageDone', 'PassageHeader', 'PassageFooter', 'PassageReady',
                    'Start', 'StoryAuthor', 'StoryBanner', 'StoryCaption', 'StoryInit',
                    'StoryInterface', 'StoryMenu', 'StorySettings', 'StoryShare',
                    'StorySubtitle', 'StoryTitle', 'StoryIncludes'}
PROJECT_TAGS = {'script', 'stylesheet', 'widget'}
PROJECT_PASSAGES_MODULE = 'stella'

# Utility

def atoi(text):
    return int(text) if text.isdigit() else text

def natural_keys(text):
    """Used for sorting in natural order.
    From http://nedbatchelder.com/blog/200712/human_sorting.html
    """
    return [atoi(c) for c in re.split('(\d+)', repr(text))]

# Passage Model

def extract_module(name):
    """Gets the name of the top-level module for the provided passage name.
    Equivalent to os.path.dirname, but for passage names.
    """
    (module_name, _, remainder) = name.partition('.')
    return (module_name, remainder)

class Passage(object):
    """Models a Twee passage."""
    def __init__(self, name, tags=None, geometry=None, content=None):
        self.name = name
        if tags is None:
            tags = []
        self.tags = tags
        if geometry is None:
            geometry = tuple()
        self.geometry = geometry
        if content is None:
            content = []
        self.content = content

    def __repr__(self):
        representation = 'Passage(' + self.name
        if self.tags:
            representation += ', tags=' + repr(self.tags)
        if self.geometry:
            representation += ', geometry=' + repr(self.geometry)
        representation += ')'

        return representation

    def __str__(self):
        return '\n'.join((self.passage_line, self.combined_content))

    @property
    def passage_line(self):
        passage_line = '::' + self.name
        if self.tags:
            passage_line += ' [' + ' '.join(self.tags) + ']'
        if self.geometry:
            passage_line += ' <' + ','.join(self.geometry) + '>'
        return passage_line

    @property
    def combined_content(self):
        return '\n'.join(self.content)

    @property
    def special_passage(self):
        return self.name in SPECIAL_PASSAGES

    @property
    def special_tags(self):
        return [tag for tag in self.tags if tag in SPECIAL_TAGS]

    @property
    def project_passage(self):
        return self.name in PROJECT_PASSAGES

    @property
    def project_tags(self):
        return [tag for tag in self.tags if tag in PROJECT_TAGS]

    @property
    def full_name(self):
        if self.project_passage or self.project_tags:
            return PROJECT_PASSAGES_MODULE + '.' + self.name
        return self.name

    @property
    def module(self):
        if self.project_passage or self.project_tags:
            return PROJECT_PASSAGES_MODULE
        return extract_module(self.name)[0]

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
    passages = []
    current_passage = None
    for line in file_lines:
        if PASSAGE_LINE.match(line) is not None:
            if current_passage is not None:
                passages.append(current_passage)
            current_passage = Passage(*parse_passage_line(line))
        else:
            if current_passage is None:
                raise ValueError('Encountered a line not belonging to any passage', line)
            else:
                current_passage.content.append(line)
    if current_passage is not None:
        passages.append(current_passage)

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

# File Processing

def process_file(file_path):
    """Splits a monolithic Twee file into a structured Twee project."""
    lines = load_file(file_path)
    passages = parse_lines(lines)
    passages = collections.OrderedDict([
        (passage.full_name, passage) for passage in sorted(passages, key=natural_keys)
        if not (passage.special_passage or passage.special_tags)
    ])
    for name in passages.keys():
        print(name)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Split a monolithic Twee file into a structured Twee project.')
    parser.add_argument('file_path', type=str, help='Path of the input file to process.')
    args = parser.parse_args()
    process_file(args.file_path)
