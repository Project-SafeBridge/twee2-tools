"""Twee2 passage model and file and passage parsing."""

import collections
import re

import util

# The regex for parsing passage header lines
PASSAGE_HEADER = re.compile('^:: *([^\[]*?) *(\[(.*?)\])? *(<(.*?)>)? *$')

# The name path delimiter
NAME_PATH_DELIMITER = '.'

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
PROJECT_PASSAGES_MODULE = 'stella'  # TODO: this should not be a constant.

def split_name(passage_name):
    """Returns the name fragment of the root of the provided passage name."""
    return (passage_name.partition(NAME_PATH_DELIMITER)[0],
            passage_name.partition(NAME_PATH_DELIMITER)[2])

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
        return '\n'.join((self.passage_header, self.combined_content))

    @property
    def passage_header(self):
        passage_header = '::' + self.name
        if self.tags:
            passage_header += ' [' + ' '.join(self.tags) + ']'
        if self.geometry:
            passage_header += ' <' + ','.join(self.geometry) + '>'
        return passage_header

    @property
    def combined_content(self):
        return '\n'.join(self.content)

    @property
    def is_special_passage(self):
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
            return PROJECT_PASSAGES_MODULE + NAME_PATH_DELIMITER + self.name
        return self.name

def parse_passage_header(line):
    """Parses a string of a passage header into data.

    Arguments:
        line: a string containing the line defining a new passage.

    Returns:
        passage_name: the name of the passage, as a string, or None if the line
        does not actually define a passage.
        tags: a list of non-empty string tags, or None if no tags were given.
        geometry: a tuple of geometry strings, or None if no geometry was given.
    """
    match = PASSAGE_HEADER.match(line)
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
        if PASSAGE_HEADER.match(line) is not None:
            if current_passage is not None:
                passages.append(current_passage)
            current_passage = Passage(*parse_passage_header(line))
        else:
            if current_passage is None:
                raise ValueError('Encountered a line not belonging to any passage', line)
            else:
                current_passage.content.append(line)
    if current_passage is not None:
        passages.append(current_passage)

    return passages

def filter_passages(passages):
    """Makes an OrderedDict of passages which should be included in a project.
    This excludes special passages and passages with special tags."""
    return collections.OrderedDict([
        (passage.full_name, passage) for passage in sorted(passages, key=util.natural_keys)
        if not (passage.is_special_passage or passage.special_tags)
    ])

def parse_file(file_path):
    """Parses a twee2 file into an OrderedDict of passages."""
    lines = util.load_file(file_path)
    return filter_passages(parse_lines(lines))

