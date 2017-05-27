"""Twee2 hierarchical project model."""

import os
import collections

import util
import passages

# The minimum additional depth inside a node the node to be a submodule
SUBMODULE_HEIGHT_THRESHOLD = 3

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

    # Information about the node

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

    # Node contents

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

    @property
    def passages(self):
        passages = []
        if self.passage is not None:
            passages.append(self.passage)
            if self.is_submodule:  # Separate retrieval for a submodule's children
                return passages
        for child in self.children.values():
            passages.extend(child.passages)
        return passages

    # Tree Insertion

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
        (name_fragment, name_remainder) = passages.split_name(passage_name)
        if name_remainder == '':
            child = self.add_child(passage_name)
            child.passage = passage
        else:
            child = self.add_child(name_fragment)
            child.add_passage(passage, name_remainder)

    # File Operations

    def reconstruct(self, root):
        if self.has_includes:
            util.mkdir_p(root)
            self.write_includes(root)
        if self.is_file and not self.is_submodule:  # Submodule file case handled below
            self.write_passages(root)
        for child in self.children.values():
            if child.is_module or child.is_submodule:
                child.reconstruct(os.path.join(root, child.name_fragment))
                if child.is_submodule and child.is_file:
                    child.write_passages(root)
            elif child.is_file:
                child.reconstruct(root)

    def write_includes(self, parent):
        with open(os.path.join(parent, 'includes.txt'), 'w') as f:
            for line in self.includes:
                f.write(line + '\n')

    def write_passages(self, parent):
        with open(os.path.join(parent, self.name_fragment + '.tw2'), 'w') as f:
            for passage in self.passages:
                f.write(str(passage) + '\n')

    # Debugging

    def print_tree(self):
        # Root node
        if self.name_fragment is None:
            for child in self.children.values():
                child.print_tree()
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
                child.print_tree()
        else:
            print(indentation + name)

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

