"""
File used for testing. 

TODO: Testing plan and motivation
- Test last 10 commits
"""
import os
from git import Repo, Git
import ast
import parsing
import pytest

# Find absolute current directory path
current_dir = os.path.dirname(os.path.abspath(__file__))

### Node Testing ###


def test_Node():  # Node abstract class
    with pytest.raises(TypeError):
        parsing.Node("test", "test")


# FolderNode instantiation
fold1 = parsing.FolderNode("dir1", None)
fold2 = parsing.FolderNode("dir2", "dir1")


@pytest.mark.parametrize("fn, n, p", [
    (fold1, "dir1", None),
    (fold2, "dir2", "dir1"),
])
def test_FolderNode(fn, n, p):
    assert fn.name == n and fn.parent == p and fn.children == []


### File structure for test repo ###
# get ast of test Python files
with open(os.path.join(current_dir, "test_repo", "a", "a.py")) as f:
    a_ast = ast.parse(f.read())

with open(os.path.join(current_dir, "test_repo", "b.py")) as f:
    b_ast = ast.parse(f.read())

file_a = parsing.FileNode("a.py", "a", a_ast)
file_b = parsing.FileNode("b.py", "test_repo", b_ast)
fold_a = parsing.FolderNode("a", "test_repo")
fold_test_repo = parsing.FolderNode("test_repo", None)
fold_a.add_child(file_a)
fold_test_repo.add_child(fold_a)
fold_test_repo.add_child(file_b)

# [test_repo]
# |____b.py
# |____[a]
#      |_____a.py


@pytest.mark.parametrize("fn, children", [
    (fold_test_repo, [fold_a, file_b]),
    (fold_a, [file_a])
])
def test_add_child(fn, children):
    for child in children:
        assert child.parent == fn.name
    assert fn.children == children

# test whether FolderNode can use Node's get_name instead of using its own
