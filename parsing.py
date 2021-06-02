"""
Initial docstring for the parsing module
"""
import os
from git import Repo, Git
import ast
import json
import pickle


with open("config.json", "r") as f:
    config = json.load(f)

repo_name = config["repo_name"]

home = os.path.expanduser("~")

def find_dir(target, start):
    """
    Finds the path of a target directory given a start directory.
    Assumes a top-down approach will be taken.

    :param target: the name of the target directory
    :type target: string

    :param start: the path of the directory where the search starts
    :type start: string 

    :rtype: string
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
g.checkout(config["branch"])
# limited to 10 for testing
commits = list(repo.iter_commits('master', max_count=config["max_count"]))


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


def create_ast_value(files):
    """
    Returns a new `tree` of Nodes based on a list of files. 

    :param files: list of files
    :type files: string list

    :rtype: Node
    """
    # create root
    root = Node(repo_name, None, None)

    for file in files:
        if file.endswith('.py'):
            # print(file)
            file_dir = file.split('/')
            file_path = os.sep.join([repo_path] + file_dir)
            with open(file_path) as fin:
                text = fin.read()
                tree = ast.parse(text)
                create_branch(root, file_dir, tree)

    return root

def create_ast_dict(commits):
    """
    Returns a dictionary mapping the SHA1 of each version in [commits] to an
    abstract syntax tree of all the Python code in that version.

    :param commits: the list of commits in a repo
    :type commits: [Commit] list

    :rtype: dictionary {keys [SHA1] : values [AST]}
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

        # create tree
        root = create_ast_value(files)

        ast_dict.update({sha1: root})

    # Side effect for testing
    print("Done.")
    return ast_dict

def update_ast_dict(dict, commits):
    """
    Updates the dictionary

    :param dict: dictionary that maps SHA1 to an AST
    :type dict: dictionary {keys [SHA1] : values [AST]} 

    :param commits: the list of commits in a repo
    :type commits: [Commit] list

    :rtype: dictionary {keys [SHA1] : values [AST]} 
    """
    
    # loop through commits
    ### Improve this
    for commit in commits: 
        sha1 = commit.hexsha
        if dict.get(sha1) == None: 
            g.checkout(sha1)
            files = g.ls_files().split('\n')
            assert files != None

            root = create_ast_value(files)

            dict.update({sha1: root})
    
    print("Done updating AST...")
    return dict

# Find current directory path 
current_dir = os.path.dirname(os.path.abspath(__file__))

try:
    print("Checking if file has been pickled...")
    with open(os.path.join(current_dir, "pickeld_ast"), "rb") as file:
        ast_dict = pickle.load(file)
    file.close()
    ast_dict = update_ast_dict(ast_dict, commits)
    print("File has been found...")
    print("Updating AST...")
except (FileNotFoundError): 
    print("Creating dictionary...")
    # Create dictionary
    ast_dict = create_ast_dict(commits)
    with open(os.path.join(current_dir, "pickeld_ast"), "wb") as file:
        pickle.dump(ast_dict, file, protocol=pickle.HIGHEST_PROTOCOL)
    file.close()

# print file structure
print("Printing the AST")
first = list(ast_dict.keys())[0]
print(ast_dict[first].to_string())
