"""
Initial docstring for the parsing module
"""

import os
from git import Repo, Git
import ast

repo_name = "snorkel"

home = os.path.expanduser("~")


def find_dir(target, start):
    """
    Returns the path of a target directory given a start directory.

    Assumes a top-down approach will be taken.
    """
    for path, dirs, files in os.walk(start):
        # If the target directory is within current list of directories
        if target in dirs:
            return os.path.join(path, target)


# Recursively determine where target repo is based on home directory
print("Finding path...")
repo_path = find_dir(repo_name, home)

try:
    os.chdir(repo_path)
except OSError:
    print("Error changing directory")

repo = Repo(repo_path)
assert not repo.bare
g = Git(repo_path)
g.checkout('master')
# limited to 10 for testing
commits = list(repo.iter_commits('master', max_count=10))


class Node():
    """
    If the Node is a leaf of a tree, an instance contains the name of a Python 
    file, its AST, and a reference to its parent directory.

    Otherwise, an instance contains the name of a directory, a reference to its
    parent directory (if any), and a list of children Nodes.
    """
    global name, tree, parent, children

    def __init__(self, n, ast, p):
        self.name = n
        self.tree = ast
        self.parent = p
        self.children = []

    def add_child(self, child):
        self.children.append(child)

    def to_string(self, level=0):
        base = self.name + "\n"
        level += 1
        for child in self.children:
            base += " "*4*level + child.to_string(level)
        return base


def create_branch(tree, filepath, ast):
    """
    Adds a leaf to `tree` to represent the file structure of the Python file
    given by `filepath`. The leaf contains the AST of the Python file.

    :param tree: the tree the branch will be added to
    :type tree: Node

    :param filepath: the path of directories to the target Python file
    :type filepath: str list

    :param ast: the AST of the target Python file
    :type ast": ast

    :rtype: Node
    """
    # the name of "folder" or Python file
    name = filepath[0]

    # if at the Python file
    if (len(filepath) == 1):
        # add AST to the leaf
        tree.add_child(Node(name, ast, tree))
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
            tree.add_child(Node(name, None, tree))
            create_branch(tree.children[-1], filepath, ast)
        return tree


def create_ast_dict(commits):
    """
    Returns a dictionary mapping the SHA1 of each version in [commits] to an
    abstract syntax tree of all the Python code in that version.
    """

    # Side effect for testing
    print("Creating ast dictionary...")

    ast_dict = {}

    for commit in commits:
        sha1 = commit.hexsha
        g.checkout(sha1)
        # get list of file paths from repo dir
        files = g.ls_files().split('\n')
        assert files != None

        # create root
        root = Node(repo_name, None, None)

        for file in files:
            if file.endswith('.py'):
                # print(file)
                file_dir = file.split('/')
                file_path = os.sep.join(
                    [repo_path] + file_dir)
                with open(file_path) as fin:
                    text = fin.read()
                    tree = ast.parse(text)
                    create_branch(root, file_dir, tree)

        ast_dict.update({sha1: root})

    # Side effect for testing
    print("Done.")
    return ast_dict


ast_dict = create_ast_dict(commits)
# print file structure
first = list(ast_dict.keys())[0]
print(ast_dict[first].to_string())


### Node Testing ###
# root = Node(repo_name, None, None)

# f1 = ["setup.py"]
# f1_path = os.sep.join([repo_path] + f1)
# with open(f1_path) as fin:
#     text = fin.read()
#     ast1 = ast.parse(text)
# t1 = create_branch(root, f1, ast1)

# f2 = ["docs", "conf.py"]
# f2_path = os.sep.join([repo_path] + f2)
# with open(f2_path) as fin:
#     text = fin.read()
#     ast2 = ast.parse(text)
# t2 = create_branch(root, f2, ast2)

# f3 = ["scripts", "check_requirements.py"]
# f3_path = os.sep.join([repo_path] + f1)
# with open(f3_path) as fin:
#     text = fin.read()
#     ast3 = ast.parse(text)
# t3 = create_branch(root, f3, ast3)

# f4 = ["scripts", "sync_api_docs.py"]
# f4_path = os.sep.join([repo_path] + f1)
# with open(f4_path) as fin:
#     text = fin.read()
#     ast4 = ast.parse(text)
# t4 = create_branch(root, f4, ast4)

# print(t4.to_string())
