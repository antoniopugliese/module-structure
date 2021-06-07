"""
This module will construct a graph representing the dependencies between files 
in a repo. It will take in tree that represents the file structure and parse the 
abstract syntax trees (AST) of each of the relevant files in order to construct 
the final graph.

Requires:
Python 3.8.3 or above. 
NetworkX 2.5 or above
"""

import ast
import os
import pickle
import Node
import parsing
import networkx as nx


repo_name = "snorkel"

# lists the name of every function in the ast


class FuncLister(ast.NodeVisitor):
    def visit_FunctionDef(self, node):
        print(node.name)
        self.generic_visit(node)


# prints the name of the function whenever it is called
class CallLister(ast.NodeVisitor):
    def visit_Call(self, node):
      # print name of function called
        print(node.func.id)
        self.generic_visit(node)


# walks through every import statement (and does nothing)
class ImportEdge(ast.NodeVisitor):
    def __init__(self):
        super().__init__()
        self.imported_mods = []

    # def visit_Import(self, node):
    #     for alias in node.names:
    #         self.imported_mods.append(alias.name)
    #     self.generic_visit(node)

    def visit_ImportFrom(self, node):
        mod = node.module
        if mod == None or mod.startswith(repo_name):
            self.imported_mods.append(node.module)
        self.generic_visit(node)


def import_relationship(tree):
    nodes = Node.traversal(tree)
    node_visitor = ImportEdge()

    for node in nodes:
        # get list of imports
        # create edges from current node to target nodes
        if type(node) is Node.FileNode:
            node_visitor.visit(node.get_ast())

            if node_visitor.imported_mods != []:
                print(f"The file '{node.name}' has the imports: ")
                for mod_name in node_visitor.imported_mods:
                    print("\t" + mod_name)
                print("\n")
                node_visitor.imported_mods = []


current_dir = os.path.dirname(os.path.abspath(__file__))

data_path = os.path.join(current_dir, "module_data")
with open(os.path.join(data_path, repo_name), "rb") as file:
    ast_dict = pickle.load(file)


first = list(ast_dict.keys())[1]
import_relationship(ast_dict[first])


class AstGraph(nx.MultiGraph):
    """
    This class represents the graph that will be constructed.
    """
