import collections
import re
import argparse

# The name path delimiter
NAME_PATH_DELIMITER = '.'

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

# The minimum additional depth inside a node the node to be a submodule
SUBMODULE_HEIGHT_THRESHOLD = 3

# Utility

def atoi(text):
    return int(text) if text.isdigit() else text

def natural_keys(text):
    """Used for sorting in natural order.
    From http://nedbatchelder.com/blog/200712/human_sorting.html
    """
    return [atoi(c) for c in re.split('(\d+)', repr(text))]

# Passage Model

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
            return PROJECT_PASSAGES_MODULE + NAME_PATH_DELIMITER + self.name
        return self.name

# Project Model

class ProjectNode(object):
    """Models a node in a Twee project tree.
    The root node should have None as its name fragment and as its parent."""
    def __init__(self, name_fragment, parent, passage=None, children=None):
        self.name_fragment = name_fragment
        self.parent = parent
        self.passage = passage
        if children is None:
            children = collections.OrderedDict()
        self.children = children

    @property
    def full_name(self):
        name = self.name_fragment
        if not self.is_root:
            parent_name = self.parent.full_name
            if parent_name:
                return '.'.join((self.parent.full_name, name))
        return name

    @property
    def depth(self):
        if self.is_root:
            return 0
        return 1 + self.parent.depth

    @property
    def height(self):
        if not self.children:
            return 0
        return 1 + max(child.height for child in self.children.values())

    @property
    def is_root(self):
        return self.parent is None

    @property
    def is_module(self):
        return self.depth == 1

    @property
    def is_submodule(self):
        return self.depth == 2 and self.height >= SUBMODULE_HEIGHT_THRESHOLD

    @property
    def is_file(self):
        if self.is_root:
            return False
        if self.parent.is_submodule:
            return True
        if self.parent.is_module:
            return (self.passage is not None) or (not self.is_submodule)
        return False

    @property
    def has_includes(self):
        return self.is_root or self.is_module or self.is_submodule

    @property
    def directories(self):
        directories = [child.name_fragment for child in self.children.values()
                       if child.is_module or child.is_submodule]
        return directories

    @property
    def files(self):
        files = [child.name_fragment for child in self.children.values()
                 if child.is_file]
        return files

    @property
    def includes(self):
        includes = [directory + '/' for directory in self.directories]
        includes.extend(self.files)
        return includes

    def add_child(self, name_fragment, overwrite=False, child=None):
        if child is not None and name_fragment != child.name_fragment:
            raise ValueError('Encountered inconsistent name fragments',
                             name_fragment, child.name_fragment)
        if overwrite or name_fragment not in self.children:
            if child is None:
                child = ProjectNode(name_fragment, parent=self)
            self.children[child.name_fragment] = child
        return self.children[name_fragment]

    def add_passage(self, passage, passage_name):
        (name_fragment, name_remainder) = split_name(passage_name)
        if name_remainder == '':
            child = self.add_child(passage_name)
            child.passage = passage
        else:
            child = self.add_child(name_fragment)
            child.add_passage(passage, name_remainder)

    def print(self):
        # Root node
        if self.name_fragment is None:
            for child in self.children.values():
                child.print()
            return

        # Non-root node
        indentation = '  ' * (self.depth - 1)
        name = self.name_fragment
        if self.is_module:
            name += ' (module)'
        if self.is_submodule:
            name += ' (submodule)'
        if self.is_file:
            name += ' (file)'
        if self.passage:
            name += ' (passage)'
        if self.children:
            print(indentation + name + ':')
            for child in self.children.values():
                child.print()
        else:
            print(indentation + name)

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

# Twee Project Structure

def populate_project_tree(passages):
    """From a flat dict of passages, makes a project tree.

    Arguments:
        passages: a flat dict of passages

    Returns:
        A ProjectNode, which is the root node of the project tree.
    """
    root = ProjectNode(None, None)
    for (passage_name, passage) in passages.items():
        root.add_passage(passage, passage_name)
    return root

# File Processing

def process_file(file_path):
    """Splits a monolithic Twee file into a structured Twee project."""
    lines = load_file(file_path)
    passages = parse_lines(lines)
    passages = collections.OrderedDict([
        (passage.full_name, passage) for passage in sorted(passages, key=natural_keys)
        if not (passage.special_passage or passage.special_tags)
    ])
    tree = populate_project_tree(passages)
    tree.print()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Split a monolithic Twee file into a structured Twee project.')
    parser.add_argument('file_path', type=str, help='Path of the input file to process.')
    args = parser.parse_args()
    process_file(args.file_path)
