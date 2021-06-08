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


# walks through every import statement
class ImportEdge(ast.NodeVisitor):
    """
    This class will display all the import statements within an AST. 
    """
    def __init__(self):
        """
        Object initializer. 
        """
        super().__init__()
        self.imported_mods = []

    # def visit_Import(self, node):
    #     for alias in node.names:
    #         self.imported_mods.append(alias.name)
    #     self.generic_visit(node)

    def visit_ImportFrom(self, node):
        self.imported_mods.append((node.module, node.level))
        self.generic_visit(node)


def in_repo(tree, starting_node, mod, level):
    """
    = "the Python module named `mod` is in the repo represented by `tree`."

    :param tree:
    :type tree:

    :param starting_node:
    :type starting_node:

    :param mod:
    :type mod:

    :param level:
    :type level:

    :rtype: bool
    """
    if (level != 0):
        # for relative imports, go up in directories according to level
        target_node = starting_node
        while (level != 0):
            target_node = Node.find_name(tree, target_node.parent)
            level -= 1
        return Node.find_name(target_node, mod.split('.')[-1] + ".py") != None
    else:
        dir_list = mod.split('.')
        root = Node.find_name(tree, dir_list[0])
        # file or folder
        return (Node.find_name(root, dir_list[-1] + ".py") != None or
                Node.find_name(root, dir_list[-1]) != None)


def import_relationship(tree):
    """
    Creates a directed edge for when a module imports another module from the
    target code repo.

    :param tree: the tree representing the target code repo
    :type tree: Node
    """
    nodes = Node.traversal(tree)
    node_visitor = ImportEdge()

    for node in nodes:
        # get list of imports
        # create edges from current node to target nodes
        if type(node) is Node.FileNode:
            node_visitor.visit(node.get_ast())

            init_node = node

            imports = []
            for mod_name in node_visitor.imported_mods:
                if in_repo(tree, node, mod_name[0], mod_name[1]):
                    imports.append(mod_name[0])
            assert node is init_node

            # <insert creating edges using imports list>

            # print imports for testing
            # full path to distinguish files with the same name
            full_name = node.name
            while (node.parent != None):
                full_name = node.parent + "\\" + full_name
                node = Node.find_name(tree, node.parent)
            print(f"The file '{full_name}' has the imports: ")
            for elem in imports:
                print(f"\t{elem}")

            node_visitor.imported_mods = []


# Get the tree of the first commit for testing
current_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(current_dir, "module_data")
with open(os.path.join(data_path, repo_name), "rb") as file:
    ast_dict = pickle.load(file)
first_tree = ast_dict[list(ast_dict.keys())[1]]


import_relationship(first_tree)

class AstGraph(nx.MultiDiGraph):
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