"""
File used for testing. 

TODO: Testing plan and motivation
- Test last 10 commits
"""
import os
from git import Repo, Git
import ast
import Node
import edge
import parsing
import networkx as nx
import pytest

# Find absolute current directory path
current_dir = os.path.dirname(os.path.abspath(__file__))

# Home directory
home = os.path.expanduser("~")

### Node Testing ###


# Node abstract class
def test_Node():
    with pytest.raises(TypeError):
        Node.Node("test", "test")


# FolderNode instantiation
fold1 = Node.FolderNode("dir1", None)
fold2 = Node.FolderNode("dir2", "dir1")


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

file_a = Node.FileNode("a.py", "a", a_ast)
file_b = Node.FileNode("b.py", "test_repo", b_ast)
fold_a = Node.FolderNode("a", "test_repo")
fold_test_repo = Node.FolderNode("test_repo", None)
fold_a.add_child(file_a)
fold_test_repo.add_child(fold_a)
fold_test_repo.add_child(file_b)

# [test_repo]
# |____b.py
# |____[a]
#      |_____a.py

graph1 = nx.Graph()
graph1.add_edge(Node.FolderNode("test_repo", "p"), Node.FileNode(
    "b.py", "p", b_ast), object=edge.DirectoryEdge("dir"))

graph2 = nx.Graph()
graph2.add_edge(Node.FolderNode("test_repo", "p"), Node.FolderNode("a", "p"))
graph2.add_edge(Node.FolderNode("a", "p"), Node.FileNode(
    "a.py", "p", a_ast), object=edge.DirectoryEdge("dir"))

graph3 = nx.Graph()
graph3.add_edges_from(graph1.edges)
graph3.add_edges_from(graph2.edges)


@pytest.mark.parametrize("g, path,ast,start_g", [
    (graph1, ["test_repo", "b.py"], b_ast, nx.Graph()),
    (graph2, ["test_repo", "a", "a.py"], a_ast, nx.Graph()),
    (graph3, ["test_repo", "a", "a.py"], a_ast, graph1),
])
def test_create_branch(g, path, ast, start_g):
    new_g = parsing.create_branch(start_g, path, ast)
    g_edges = list(map(lambda e: edge_to_string(*e), g.edges))
    new_g_edges = list(map(lambda e: edge_to_string(*e), new_g.edges))
    assert g_edges == new_g_edges


@pytest.mark.parametrize("fn, children", [
    (fold_test_repo, [fold_a, file_b]),
    (fold_a, [file_a])
])
def test_add_child(fn, children):
    for child in children:
        assert child.parent == fn.name
    assert fn.children == children


# get_name() from Node class
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
    (fold_test_repo, "test_repo\n    a\n        a.py\n    b.py\n"),
    (fold_a, "a\n    a.py\n"),
    (file_b, "b.py\n"),
    (file_a, "a.py\n")
])
def test_to_string(fn, output):
    assert fn.to_string() == output


# traversal()
@pytest.mark.parametrize("fn, nodes", [
    (fold_test_repo, [fold_test_repo, fold_a, file_b, file_a]),
    (fold_a, [fold_a, file_a]),
    (file_b, [file_b]),
    (file_a, [file_a])
])
def test_traversal(fn, nodes):
    assert Node.traversal(fn) == nodes


# find_name()
@pytest.mark.parametrize("fn, name, node", [
    (fold_test_repo, "test_repo", fold_test_repo),
    (fold_test_repo, "a", fold_a),
    (fold_test_repo, "a.py", file_a),
    (fold_test_repo, "b.py", file_b),
    (fold_test_repo, "c.py", None),
    (fold_a, "test_repo", None),
    (fold_a, "a.py", file_a),
    (file_b, "test_repo", None),
    (file_b, "b.py", file_b),
])
def test_find_name(fn, name, node):
    assert Node.find_name(fn, name) is node


# find_ast()
@pytest.mark.parametrize("fn, name, ast", [
    (fold_test_repo, "test_repo", None),
    (fold_test_repo, "a.py", a_ast),
    (fold_test_repo, "b.py", b_ast),
    (fold_test_repo, "c.py", None),
    (fold_a, "a.py", a_ast),
    (file_b, "b.py", b_ast),
])
def test_find_ast(fn, name, ast):
    assert Node.find_ast(fn, name) is ast
