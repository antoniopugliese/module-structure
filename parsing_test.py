"""
File for testing parsing.py module.

TODO: Testing plan and motivation
- Test last 10 commits
"""
import os
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

### File structure for test repo ###
# get ast of test Python files
with open(os.path.join(current_dir, "test_repo", "a", "a.py")) as f:
    a_ast = ast.parse(f.read())
with open(os.path.join(current_dir, "test_repo", "b.py")) as f:
    b_ast = ast.parse(f.read())

# [test_repo]
# |____b.py
# |____[a]
#      |_____a.py

repo_fold_node = ("test_repo", Node.FolderNode("test_repo", "p"))
b_file_node = ("test_repo\\b.py", Node.FileNode("b.py", "p", b_ast))
a_fold_node = ("test_repo\\a", Node.FolderNode("a", "p"))
a_file_node = ("test_repo\\a\\a.py", Node.FileNode("a.py", "p", a_ast))

# Construct test graphs
graph1 = nx.MultiDiGraph()
graph1.add_node(repo_fold_node[0], node=repo_fold_node[1])
graph1.add_node(b_file_node[0], node=b_file_node[1])
graph1.add_edge("test_repo", "test_repo\\b.py",
                object=edge.DirectoryEdge("dir"))

graph2 = nx.MultiDiGraph()
graph2.add_node(repo_fold_node[0], node=repo_fold_node[1])
graph2.add_node(a_fold_node[0], node=a_fold_node[1])
graph2.add_node(a_file_node[0], node=a_file_node[1])
graph2.add_edge("test_repo", "test_repo\\a",
                object=edge.DirectoryEdge("dir"))
graph2.add_edge("test_repo\\a", "test_repo\\a\\a.py",
                object=edge.DirectoryEdge("dir"))

graph3 = nx.MultiDiGraph()
graph3.add_edges_from(graph1.edges)
graph3.add_edges_from(graph2.edges)


# test create_branch()
@pytest.mark.parametrize("g, path,ast,start_g", [
    (graph1, ["test_repo", "b.py"], b_ast, nx.MultiDiGraph()),
    (graph2, ["test_repo", "a", "a.py"], a_ast, nx.MultiDiGraph()),
    (graph3, ["test_repo", "a", "a.py"], a_ast, graph1),
])
def test_create_branch(g, path, ast, start_g):
    new_g = parsing.create_branch(start_g, path, ast)
    assert list(g.edges) == list(new_g.edges)


# test create_ast_graph
@pytest.mark.parametrize("g, files, repo_path, repo_name", [
    (graph3, ["b.py", "a/a.py"], os.path.join(
        current_dir, "test_repo"), "test_repo")
])
def test_create_ast_graph(g, files, repo_path, repo_name):
    new_g = parsing.create_ast_graph(files, repo_path, repo_name)
    print(list(new_g.edges))
    assert (list(g.nodes) == list(new_g.nodes)) and (
        list(g.edges) == list(new_g.edges))
