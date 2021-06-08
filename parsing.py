"""
This module constructs an object representing the file structure and the abstract
syntax tree (AST) for every Python code file in a given git repo.

This module creates a dictionary object mapping the SHA1 hash of a commit of a git
repo to a custom object that maintains information about the directory of the git
repo, and the AST of every Python code file. A user can modify the ``config.json``
file to alter what commits are analyzed.

Requires Python 3.8.3 or above. 
"""
import os
from git import Repo, Git
import ast
import json
import pickle
import Node
import edge
from abc import ABC, abstractmethod


class Node(ABC):
    """
    This abstract Node class is extended to build a tree that represents a software
    module. The Node subclasses represent either a folder or Python file.
    """

    def __init__(self, n, p):
        """
        Initializes the Node object.

        :param n: name of the instance (file or directory)
        :type n: str

        :param p: the name of the parent of the Node object, None if doesn't exist
        :type p: str

        :return: A Node object containing n and p.
        :rtype: Node
        """
        self.name = n
        self.parent = p

    @abstractmethod
    def to_string(self, level=0):
        pass

    def get_name(self):
        """
        Getter method to return the name of the Node.

        :return: name of Node
        :rtype: str
        """
        return self.name


class FolderNode(Node):
    """
    The Node subclass that represents a directory. It contains a ``children``
    attribute that stores its child Nodes, which may be files or other directories.
    """

    def __init__(self, n, p):
        """
        Initializes the FolderNode with no children Nodes.

        :param n: name of the directory.
        :type n: str

        :param p: the name of the parent directory, None if this directory is root folder.
        :type p: str

        :return: A FolderNode object containing `n` and `p`.
        :rtype: FolderNode

        >>> FolderNode('example', None)
        >>> FolderNode('child', 'example')
        """
        super().__init__(n, p)
        self.children = []

    def add_child(self, child):
        """
        Adds a child to the FolderNode object.

        :param child: Node object to add to the FolderNode.
        :type child: Node

        :return: FolderNode object with child added to its list of children.
        :rtype: FolderNode

        >>> example = FolderNode('example', None)
        >>> example.add_child(FolderNode('child_1', 'example'))
        >>> example.add_child(FolderNode('child_2', 'example'))
        >>> example.children
        [FolderNode('child_1', 'example'), FolderNode('child_2', 'example')]
        """
        self.children.append(child)

    def to_string(self, level=0):
        """
        The string representation of the FolderNode and all of its children Nodes.
        Mainly intended for debugging purposes.

        :param level: the current depth of the Node, defaults to 0.
        :type level: int

        :return: A string representing the FolderNode and all its children.
        :rtype: str

        >>> example = FolderNode('src', None)
        >>> example.to_string()
        'src'

        >>> example.add_child(FolderNode('child', 'src'))
        >>> example.add_child(FileNode('code.py', 'src', 'ast'))
        >>> example.to_string()
        'src'
            'child'
            'code.py'
        """
        base = self.name + "\n"
        level += 1
        for child in self.children:
            base += " "*4*level + child.to_string(level)
        return base

    def get_children(self):
        """
        Getter method for the children of the Node

        :return: the list of children from the Node
        :rtype: Node list
        """
        return self.children


class FileNode(Node):
    """
    The Node subclass that represents a Python file. It contains a ``tree``
    attribute that stores the abstract syntax tree (AST) of the Python file it
    represents. A FileNode cannot have any children Nodes (it must be a leaf).
    """

    def __init__(self, n, p, ast):
        """
        Initializes the FileNode with the AST of the Python file given by `n`.

        :param n: name of the Python file.
        :type n: str

        :param p: the name of the parent directory, if any.
        :type p: str

        :param ast: the AST of the Python file.
        :type ast: ast

        :return: A FileNode object containing `n`, `p`, and `ast`.
        :rtype: FileNode
        """
        super().__init__(n, p)
        self.tree = ast

    def to_string(self, level=0):
        """
        The string representation of the FileNode. Mainly intended for debugging purposes.

        :param level: the current depth of the Node, defaults to 0.
        :type level: int

        :return: the name of the Python file.
        :rtype: str

        >>> FileNode("code.py","root","ast").to_string()
        'code.py'
        """
        return self.name + "\n"

    def get_ast(self):
        """
        Getter method to return the abstract syntax tree of the file.

        :return: AST of file
        :rtype: ast
        """
        return self.tree


def traversal(root):
    """
    Traverses the tree using a breadth-first-search approach.

    :param root: the root of the tree
    :type root: Node

    :return: list of all the Nodes in the tree
    :rtype: Node list
    """
    if root is None:
        return []

    visited = [root]
    queue = [root]

    while queue:
        curr_node = queue.pop(0)

        if type(curr_node) is FileNode:
            if curr_node not in visited:
                visited.append(curr_node)
        else:
            for child in curr_node.get_children():
                if child not in visited:
                    visited.append(child)
                    queue.append(child)

    return visited


def find_name(root, n):
    """
    Finds a Node with name n in a tree starting at the root.

    :param root: the root of the tree
    :type root: Node

    :param n: the name of the Node
    :type n: str

    :return: the Node with name n, None if not found
    :rtype: Node
    """
    if root is None:
        return None

    visited = [root.get_name()]
    queue = [root]

    while queue:
        curr_node = queue.pop(0)
        curr_name = curr_node.get_name()

        if curr_name == n:
            return curr_node

        if type(curr_node) is FolderNode:
            if curr_node not in visited:
                for child in curr_node.get_children():
                    visited.append(child.get_name())
                    queue.append(child)
        else:
            continue

    return None


def find_ast(root, n):
    """
    Finds the abstract syntax tree of file with name `n` in a tree starting at
    root. If the file cannot be found, return None.

    :param root: the root of the tree
    :type root: Node

    :param n: the name of the file
    :type n: str

    :return: the ast of file n
    :rtype: ast.Module
    """
    node = find_name(root, n)

    if node is None or type(node) is FolderNode:
        return None

    return node.get_ast()


def find_dir(start, target):
    """
    Finds the path of a target directory given a start directory.
    Assumes a top-down approach will be taken.

    :param start: the path of the directory where the search starts
    :type start: str

    :param target: the name of the target directory
    :type target: str

    :return: path of the target directory
    :rtype: str

    >>> home = os.path.expanduser("~")
    >>> repo_name = 'snorkel'
    >>> find_dir(home, repo_name)
    'C:\\Users\\Antonio\\Documents\\GitHub\\snorkel'
    """
    for path, dirs, files in os.walk(start):
        # If the target directory is within current list of directories
        if target in dirs:
            return os.path.join(path, target)


def create_branch(tree, filepath, ast):
    """
    Adds a leaf to `tree` to represent the file structure of the Python file
    given by `filepath`. The leaf contains the AST of the Python file.

    :param tree: the existing tree the branch will be added to
    :type tree: Node

    :param filepath: the sequence of directories to the target Python file
    :type filepath: str list

    :param ast: the AST object of the target Python file
    :type ast: ast

    :return: leaf to the `tree` that contains the AST of the Python file
    :rtype: Node
    """
    # the name of "folder" or Python file
    name = filepath[0]

    # if at the Python file
    if (len(filepath) == 1):
        # add AST to the leaf
        tree.add_child(Node.FileNode(name, tree.name, ast))
        return tree
    else:
        filepath.pop(0)
        branch_exists = False
        # if "folder" already is in the tree, add the branch starting from that
        # folder
        for child in tree.children:
            if (child.name == name):
                create_branch(child, filepath, ast)
                branch_exists = True
                break
        # create the "folder", and then add the branch
        if (not branch_exists):
            tree.add_child(Node.FolderNode(name, tree.name))
            create_branch(tree.children[-1], filepath, ast)
        return tree


def create_ast_value(files, repo_path, repo_name):
    """
    Creates a new `tree` of Nodes based on a list of files. 

    :param files: list of files
    :type files: str list

    :param repo_path: the path to the directory that contains the target repo
    :type repo_path: str

    :param repo_name: the name of the target repo
    :type repo_name: str

    :return: a `tree` of Nodes based on the files in repo_path
    :rtype: Node
    """
    # create root
    root = Node.FolderNode(repo_name, None)

    for file in files:
        if file.endswith('.py'):
            # print(file)
            file_dir = file.split('/')
            file_path = os.sep.join([repo_path] + file_dir)
            with open(file_path) as fin:
                text = fin.read()
                try:
                    tree = ast.parse(text)
                    create_branch(root, file_dir, tree)
                except SyntaxError:
                    pass
                    # if the code that ast parses has a syntax error, it causes
                    # the function call to result in a syntax error.

    return root


def create_ast_dict(commits, repo_path, repo_name, g):
    """
    Creates a dictionary mapping the SHA1 of each version in `commits` to a Node
    object that contains the abstract syntax trees of all the Python code in that
    version.

    :param commits: the list of commits in a repo
    :type commits: Git.Commit list

    :param repo_path: the path to the directory that contains the target repo
    :type repo_path: str

    :param repo_name: the name of the target repo
    :type repo_name: str

    :param g: the git module to analyze
    :type g: Git

    :return: a dictionary mapping the SHA1 of each commit to a Node object. 
    :rtype: dictionary {str : Node}
    """

    # Side effect for testing
    print("Creating ast dictionary...", end="", flush=True)

    ast_dict = {}

    for commit in commits:
        sha1 = commit.hexsha
        g.checkout(sha1)
        # get list of file paths from repo dir
        files = g.ls_files().split('\n')
        assert files != None

        # create tree
        root = create_ast_value(files, repo_path, repo_name)

        ast_dict.update({sha1: root})

    # Side effect for testing
    print("Done")
    return ast_dict


def update_ast_dict(dict, commits, repo_path, repo_name, g):
    """
    Updates the dictionary to add any new commits in a repo. 

    :param dict: dictionary that maps SHA1 to a Node object
    :type dict: dictionary {str : Node} 

    :param commits: the list of commits in a repo
    :type commits: Git.Commit list

    :param repo_path: the path to the directory that contains the target repo
    :type repo_path: str

    :param repo_name: the name of the target repo
    :type repo_name: str

    :param g: the git module to analyze
    :type g: Git

    :return: An updated dictionary with any new commits. 
    :rtype: dictionary {str : Node} 
    """

    # loop through commits
    # Improve this

    print("Updating the dictionary...", end="", flush=True)
    for commit in commits:
        sha1 = commit.hexsha
        if dict.get(sha1) == None:
            g.checkout(sha1)
            files = g.ls_files().split('\n')
            assert files != None

            root = create_ast_value(files, repo_path, repo_name)

            dict.update({sha1: root})

    print("Done")
    return dict
