"""
File for testing relationship.py module.
"""
import os
import ast
import Node
import edge
import parsing
import relationship
import networkx as nx
import pytest

# @pytest.mark.parametrize("fn, children", [
#     (fold_test_repo, [fold_a, file_b]),
#     (fold_a, [file_a])
# ])
# def test_add_child(fn, children):
#     for child in children:
#         assert child.parent == fn.name
#     assert fn.children == children
