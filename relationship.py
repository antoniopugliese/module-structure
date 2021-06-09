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
import edge
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


class CallLister(ast.NodeVisitor):
    """
    This class gathers all function calls within an AST.
    """

    def __init__(self):
        """
        Object initializer. A CallLister intialized this way will gather all
        function calls in the AST.
        """
        super().__init__()
        self.calls = []

    def visit_Call(self, node):
        """
        Gathers all called function's names. 

        :param node: a node within an AST.
        :type node: AST Node   
        """
        if type(node.func) is ast.Name:
            self.calls.append(node.func.id)

        elif type(node.func) is ast.Attribute:
            self.calls.append(node.func.attr)
        self.generic_visit(node)


class ClassLister(ast.NodeVisitor):
    """
    This class gathers all class defintion in an AST, as well as the base classes
    used.
    """

    def __init__(self):
        """
        Object initializer. 
        """
        super().__init__()
        self.classes = []
        self.extends = []

    def visit_ClassDef(self, node: ast.ClassDef):
        """
        Gathers the name of every defined class, as well as the classes they extend.
        """
        self.classes.append(node.name)
        for b in node.bases:
            if type(b) is ast.Name:
                self.extends.append(b.id)
            elif type(b) is ast.Attribute:
                self.extends.append(b.value.id)


class ImportLister(ast.NodeVisitor):
    """
    This class will gathers all the import statements within an AST, as well as
    the functions the statements import, if any. 
    """

    def __init__(self):
        """
        Object initializer. 
        """
        super().__init__()
        self.imported_mods = []
        self.imported_funcs = {}

    # def visit_Import(self, node):
    #     for alias in node.names:
    #         self.imported_mods.append(alias.name)
    #     self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """
        Gathers the imported modules and imported functions, or their alias if used.
        """
        self.imported_mods.append((node.module, node.level))
        funcs = []
        for a in node.names:
            if a.asname != None:
                funcs.append(a.asname)
            else:
                funcs.append(a.name)

        self.imported_funcs.update({node.module: funcs})

        self.generic_visit(node)


def in_repo(graph: nx.MultiDiGraph, starting_node, mod, level):
    """
    = "the Python module named `mod` is in the repo represented by `graph`."

    :param graph: the graph representing the target repo
    :type graph: networkx.MultiDiGraph

    :param starting_node: the name of the node to start the search from
    :type starting_node: str

    :param mod: the name of the target Python module (with the extension '.py')
    :type mod: str

    :param level: the level of the relative import (level=0 means an absolute import)
    :type level: int

    :rtype: bool
    """
    if (level != 0):
        # for relative imports, go up in directories according to level
        target_node = starting_node
        while (level != 0):
            # each node only has one direct predeccesor
            target_node = list(graph.predecessors(target_node))[0]
            level -= 1
        for node in nx.bfs_successors(graph, target_node):
            if node[0].endswith(target_node):
                return True
        return False
    else:
        # for absolute imports, search to see if module in graph
        # dir_list = mod.split('.')
        # target_node = os.path.join(*dir_list)
        target_node = mod.replace('.', os.sep)
        for node in graph.nodes:
            if target_node in node:
                return True
        return False


def import_relationship(graph):
    """
    Creates a directed edge for when a module imports another module from the
    target code repo.

    :param graph: the tree representing the target code repo
    :type graph: networkx.MultiDiGraph
    """
    node_visitor = ImportLister()

    for node in graph.nodes:
        # get the 'node' attribute of the graph node named node (confusing)
        curr_node = graph.nodes[node]["node"]
        if type(curr_node) is Node.FileNode:  # if at Python file
            node_visitor.visit(curr_node.get_ast())

            imports = []
            for mod_name in node_visitor.imported_mods:
                if in_repo(graph, node, mod_name[0], mod_name[1]):
                    imports.append(mod_name[0])

            # <insert creating edges using imports list>

            # print imports for testing
            print(f"The file '{node}' has the imports: ")
            for elem in imports:
                print(f"\t{elem}")

            node_visitor.imported_mods = []


def imports_dict(graph):
    """
    Creates a dictionary of imported functions. 

    :param graph: the tree representing the target code repo
    :type graph: networkx.MultiDiGraph

    :returns: A dictionary mapping the name of a Python file to a list of all 
    modules it imports from its own repo, which is represented by `graph`.
    :rtype: dict {str : str list}
    """
    import_dict = {}
    node_visitor = ImportLister()

    for node in graph.nodes:
        # get the 'node' attribute of the graph node named node (confusing)
        curr_node = graph.nodes[node]["node"]
        if type(curr_node) is Node.FileNode:  # if at Python file
            node_visitor.visit(curr_node.get_ast())

            imports = []
            for mod_name in node_visitor.imported_mods:
                if in_repo(graph, node, mod_name[0], mod_name[1]):
                    imports.append(node_visitor.imported_funcs[mod_name[0]])
            import_dict.update({node: imports})

            node_visitor.imported_mods = []

    return import_dict


def function_call_relationship(graph):
    """
    Creates a directed edge for when a module calls a function from another module 
    from the target code repo.

    :param graph: the graph representing the target code repo
    :type graph: networkx.MultiDiGraph
    """
    import_dict = imports_dict(graph)
    node_visitor = CallLister()

    for node in graph.nodes:
        # get the 'node' attribute of the graph node named node (confusing)
        curr_node = graph.nodes[node]["node"]
        if type(curr_node) is Node.FileNode:  # if at Python file
            node_visitor.visit(curr_node.get_ast())

            imported_calls = []
            for func in node_visitor.calls:
                for imported_func in import_dict[node]:
                    if func in imported_func:
                        imported_calls.append(func)

            print(f"The file '{node}' calls functions: ")
            print(f"\tImported calls:{imported_calls}")
            # print(import_dict[node])  # list of lists
            #print(f"\tAll calls:{node_visitor.calls}")
            node_visitor.calls = []


def inheritance_relationships(graph):
    """
    """
    node_visitor = ClassLister()

    for node in graph.nodes:
        # get the 'node' attribute of the graph node named node (confusing)
        curr_node = graph.nodes[node]["node"]
        if type(curr_node) is Node.FileNode:  # if at Python file
            node_visitor.visit(curr_node.get_ast())

            print(f"The file '{node}' defines classes: ")
            print(f"\t{node_visitor.classes}")
            print(f"\tthat extend the classes:")
            print(f"\t\t{node_visitor.extends}")

            node_visitor.classes = []
            node_visitor.extends = []


# Get the tree of the first commit for testing
current_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(current_dir, "module_data")
with open(os.path.join(data_path, repo_name), "rb") as file:
    ast_dict = pickle.load(file)
first_tree = ast_dict[list(ast_dict.keys())[0]]

# import_relationship(first_tree)
function_call_relationship(first_tree)
# inheritance_relationships(first_tree)


class AstGraph(nx.MultiDiGraph):
    """
    This class represents the graph that will be constructed.

    By design, this class will extend the NetworkX MultiDiGraph in order to
    represent the connections and dependencies between modules. The nodes of the 
    graph will represent each file within the a repo directory. A directed edge 
    from one node to another will represent the dependency that a node has. 
    """

    def __init__(self, commit=None):
        """
        Initializes the graph object. 

        :param commit: the current commit history of the repo
        :type commit: str
        """
        super().__init__()
        self.commit = None

    def add_node(self, node_for_adding, **attr):
        """
        Adds a node to the graph. 
        TODO: properly tie the **attr to attributes for the graph
        """
        return super().add_node(node_for_adding, **attr)

    def add_edge(self, u, v, key, **attr):
        """
        Adds a directed edge from `u` to `v`. 
        TODO: properly tie the **attr to attributes for the graph
        """
        return super().add_edge(u, v, key=key, **attr)

    def get_edge_data(self, u, v, key, default):
        """
        Gets the edge data from `u` to `v`. 
        TODO: Display all the edges depending on the type of edge based on the
        edge module
        """
        return super().get_edge_data(u, v, key=key, default=default)
