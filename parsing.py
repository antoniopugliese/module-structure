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
import networkx as nx
from abc import ABC, abstractmethod

# add edges, it ignores those that are already there
# edgeweight Class
# FileNode,FolderNode


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


def create_branch(graph, filepath, ast):
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

    # add folders
    i = 0
    base = filepath[0]

    while i < len(filepath) - 2:
        next_dir = os.path.join(base, filepath[i + 1])
        graph.add_node(base, node=Node.FolderNode(base, "p"))
        graph.add_node(next_dir, node=Node.FolderNode(next_dir, "p"))
        graph.add_edge(base, next_dir, object=edge.DirectoryEdge("dir"))
        base = next_dir
        i += 1

    # add python file
    next_dir = os.path.join(base, filepath[i + 1])
    graph.add_node(next_dir, node=Node.FileNode(next_dir, "p", ast))
    graph.add_edge(base, next_dir, object=edge.DirectoryEdge("dir"))

    return graph


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

    graph = nx.MultiDiGraph()

    # create root node
    graph.add_node(repo_name, node=Node.FolderNode(repo_name, None))

    for file in files:
        if file.endswith('.py'):
            # print(file)
            file_dir = file.split('/')
            file_path = os.sep.join([repo_path] + file_dir)
            with open(file_path) as fin:
                text = fin.read()
                try:
                    tree = ast.parse(text)
                    # print(file_dir)
                    create_branch(graph, [repo_name] + file_dir, tree)
                except SyntaxError:
                    pass
                    # if the code that ast parses has a syntax error, it causes
                    # the function call to result in a syntax error.

    return graph


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

        # create graph
        graph = create_ast_value(files, repo_path, repo_name)

        ast_dict.update({sha1: graph})

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


def print_graph(graph):
    def edge_to_string(n1, n2, o):
        return (n1.name, n2.name)
    for n in list(graph.nodes):
        print("\t" + n)
