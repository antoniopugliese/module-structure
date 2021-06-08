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

class FuncLister(ast.NodeVisitor):
    """
    This class will display all the functions within an AST. 
    """
    def visit_FunctionDef(self, node):
        """
        Visits and prints all the function definitions in an AST.

        :param node: a node within an AST.
        :type node: AST Node   
        """
        print(node.name)
        self.generic_visit(node)


# prints the name of the function whenever it is called
class CallLister(ast.NodeVisitor):
    """
    This class will display whenever a function is called within an AST.
    """
    def visit_Call(self, node):
        """
        Visits and prints all the function calls in an AST. 

        :param node: a node within an AST.
        :type node: AST Node   
        """
        print(node.func.id)
        self.generic_visit(node)


# walks through every import statement (and does nothing)
class ImportEdge(ast.NodeVisitor):
    """
    This class will display all the import statements within an AST. 
    """
    def __init__(self):
        """
        Class initializer. 
        """
        super().__init__()
        self.imported_mods = []

    # def visit_Import(self, node):
    #     for alias in node.names:
    #         self.imported_mods.append(alias.name)
    #     self.generic_visit(node)

    def visit_ImportFrom(self, node):
        """
        Visits and displays all the `from [module] import [package]` statements 
        within an AST. 

        :param node: a node within an AST.
        :type node: AST Node   
        """
        mod = node.module
        if mod == None or mod.startswith(repo_name):
            self.imported_mods.append(node.module)
        self.generic_visit(node)


def import_relationship(tree):
    """
    This function displays all the imports for each file within a parsed tree. 

    :param tree: represents the file structure and contains the ASTs of each 
    relevant file.
    :type tree: Node.FolderNode
    """
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

    By design, this class will extend the NetworkX MultiDiGraph in order to
    represent the connections and dependencies between modules. The nodes of the 
    graph will represent each file within the a repo directory. A directed edge 
    from one node to another will represent the dependency that a node has. 
    """

    def __init__(self, commit = None):
        """
        Initializes the graph object. 

        :param commit: the current commit history of the repo
        :type commit: str
        """
        super().__init__()
        self.commit = None