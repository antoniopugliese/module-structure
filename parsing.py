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
repo_path = find_dir(repo_name, home)

# Get path and change directory
# Works if target directory is same depth as current directory
# git_path = os.getcwd().split(os.sep)[:-1]
# git_path.append(repo_name)
# repo_path = os.sep.join(git_path)

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


def create_ast_dict(commits):
    """
    Returns a dictionary mapping the SHA1 of each version in [commits] to an
    abstract syntax tree of all the Python code in each version.
    """

    # Side effect for testing
    print("Creating ast dictionary...")

    ast_dict = {}

    for commit in commits:
        sha1 = commit.hexsha
        g.checkout(sha1)
        files = g.ls_files()
        assert files != None

        # create empty ast
        root = ast.parse("")

        for file in files.split('\n'):
            if file.endswith('.py'):
                file_path = os.sep.join(
                    [repo_path] + file.split('/'))
                # print(file_path)
                with open(file_path) as fin:
                    text = fin.read()
                    tree = ast.parse(text)
                    # combining tree bodies loses the separation between modules,
                    # but combines all python code into one single AST
                    root.body += tree.body

        ast_dict.update({sha1: root})

    # Side effect for testing
    print("Done.")
    return ast_dict


ast_dict = create_ast_dict(commits)
print(ast_dict)
