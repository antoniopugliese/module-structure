"""
Testing for node module. 
"""
import os
import ast
import node
import pytest

# Find absolute current directory path
current_dir = os.path.dirname(os.path.abspath(__file__))

# Home directory
home = os.path.expanduser("~")

### node Testing ###


# node abstract class
def test_Node():
    with pytest.raises(TypeError):
        node.Node("test", "test")


# FolderNode instantiation
fold1 = node.FolderNode("dir1")
fold2 = node.FolderNode("dir2")


@pytest.mark.parametrize("fn, n", [
    (fold1, "dir1"),
    (fold2, "dir2"),
])
def test_FolderNode(fn, n):
    assert fn.name == n


### File structure for test repo ###
# get ast of test Python files
with open(os.path.join(current_dir, "test_repo", "a", "a.py")) as f:
    a_ast = ast.parse(f.read())

with open(os.path.join(current_dir, "test_repo", "b.py")) as f:
    b_ast = ast.parse(f.read())

file_a = node.FileNode("a.py", a_ast)
file_b = node.FileNode("b.py", b_ast)
fold_a = node.FolderNode("a")
fold_test_repo = node.FolderNode("test_repo")

# [test_repo]
# |____b.py
# |____[a]
#      |_____a.py


# get_name() from node class
@pytest.mark.parametrize("fn, name", [
    (fold_test_repo, "test_repo"),
    (fold_a, "a"),
    (file_a, "a.py"),
    (file_b, "b.py")
])
def test_get_name(fn, name):
    assert fn.get_name() == name


# to_string()
@pytest.mark.parametrize("fn, output", [
    (fold_test_repo, "test_repo"),
    (fold_a, "a"),
    (file_b, "b.py"),
    (file_a, "a.py")
])
def test_to_string(fn, output):
    assert fn.to_string() == output
