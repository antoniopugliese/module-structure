"""
This module will construct a graph representing the dependencies between files
in a repo. It will take in the tree that represents the file structure and parse the
abstract syntax trees (AST) of each of the relevant files in order to construct
the final graph.

Requires:
Python 3.8.3 or above.
"""

import ast
import os
from node import FileNode, FolderNode, ClassNode, FuncNode
import edge
import networkx as nx


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

    def reset(self):
        """
        Clears the list of visited nodes.
        """
        self.calls = []


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
        self.extends = {}

    def visit_ClassDef(self, node: ast.ClassDef):
        """
        Gathers the name of every defined class, as well as the classes they extend.

        :param node: the starting node (represents a class)
        :type node: ast.ClassDef

        """
        self.classes.append(node.name)
        bases = []
        for b in node.bases:
            if type(b) is ast.Name:
                bases.append(b.id)
            elif type(b) is ast.Attribute:
                bases.append(b.value.id)
        self.extends.update({node.name: bases})
        self.generic_visit(node)

    def reset(self):
        """
        Clears the list of class definitions and class extensions.
        """
        self.classes = []
        self.extends = {}


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
    #     """
    #     Gathers the imported modules and imported functions, or their alias if used.
    #     """
    #     # imports using this statement are from the same directory (level = 1)
    #     for alias in node.names:
    #         if alias.asname != None:
    #             self.imported_mods.append((alias.asname, 1))
    #         else:
    #             self.imported_mods.append((alias.name, 1))
    #     self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """
        Gathers the imported modules and imported functions, or their alias if used.

        :param node: the node that represents an import
        :type node: ast.ImportFrom
        """
        self.imported_mods.append((node.module, node.level))
        funcs = []
        for a in node.names:
            if a.asname != None:
                funcs.append(a.asname)
            else:
                funcs.append(a.name)

        self.imported_funcs.update({node.module: funcs})

    def reset(self):
        """
        Clears the list of imported modules.
        """
        self.imported_mods = []
        self.imported_funcs = {}


class DefinitionLister(ast.NodeVisitor):
    """
    This class will gather classes and functions defined within an AST, and add
    Node object representations of them to an existing root.
    """

    def __init__(self, root):
        """
        The root to add the ClassNode and FuncNode.

        :param root: the FileNode object corresponding to the Python file of the AST.
        :type root: Node
        """
        super().__init__()
        # copy the graph to make sure original data is preserved
        self.graph = nx.MultiDiGraph()
        self.graph.add_edges_from(root.edges.data())
        self.starting_node = None

    def visit_ClassDef(self, node):
        """
        Adds a ClassNode to the graph, as well as any functions defined in the class.

        :param node: a node that represents a class definition
        :type node: ast.ClassDef
        """
        class_name = os.path.join(self.starting_node.name, node.name)
        class_node = ClassNode(class_name, node)
        self.graph.add_edge(self.starting_node, class_node,
                            edge=edge.DefinitionEdge(""))

        # Add FuncNodes as children of this ClassNode
        old_starting_node = self.starting_node
        self.starting_node = class_node
        self.generic_visit(node)
        self.starting_node = old_starting_node

    def visit_FunctionDef(self, node):
        """
        Adds a FuncNode to the graph.

        :param node: a node representing the function definition.
        :type node: ast.FunctionDef
        """
        func_name = os.path.join(self.starting_node.name, node.name)
        self.graph.add_edge(self.starting_node, FuncNode(
            func_name, node), edge=edge.DefinitionEdge(""))
        self.generic_visit(node)


def get_repo_node(graph: nx.MultiDiGraph, starting_node, mod, level):
    """
    Finds the FileNode object associated with the module name ``mod``, if any.

    :param graph: the graph representing the target repo
    :type graph: networkx.MultiDiGraph

    :param starting_node: the name of the node to start the search from
    :type starting_node: str

    :param mod: the name of the target Python module
    :type mod: str

    :param level: the level of the relative import (level=0 means an absolute import)
    :type level: int

    :rtype: FileNode
    """
    if (level != 0):
        # print(f"relative for {mod}")
        # for relative imports, go up in directories according to level
        target_node = starting_node
        while (level != 0):
            # each node only has one direct predeccesor
            target_node = list(graph.predecessors(target_node))[0]
            level -= 1
        # after reaching top directory, search successors recursively for target
        for node in graph.successors(target_node):
            n = node.get_name()
            if n.endswith(mod) or n.endswith(mod + ".py"):
                return node
        return None
    else:
        # for absolute imports, search to see if module in graph
        target_node_name = mod.replace('.', os.sep)
        for node in graph.nodes:
            n = node.get_name()
            if n.endswith(target_node_name) or n.endswith(target_node_name + ".py"):
                return node
        return None


def import_relationship(graph: nx.MultiDiGraph):
    """
    Creates a directed edge for when a module imports another module from the
    target code repo.

    :param graph: the tree representing the target code repo
    :type graph: networkx.MultiDiGraph
    """
    node_visitor = ImportLister()
    imports = []

    # collect all edges to be added
    for node in graph.nodes:
        if type(node) is FileNode:  # if at Python file
            node_visitor.visit(node.get_ast())

            # add every import that is from within the repo
            for (name, level) in node_visitor.imported_mods:
                imported_node = get_repo_node(graph, node, name, level)
                if imported_node is not None:  # if exists
                    imports.append((node, imported_node, {
                                   'edge': edge.ImportEdge("")}))

            node_visitor.reset()

    # add collected edges
    graph.add_edges_from(imports)


# return a list of nodes corresponding to functions in a module
def get_func_nodes(graph, parent_node, n_list):
    """
    Gives the list of Node objects corresponding to the names in ``n_list``.

    :param graph: the graph to search for the nodes in
    :type graph: networkx.MultiDiGraph

    :param parent_node: the Node object in the graph to begin the search from
    :type parent_node: Node

    :param n_list: the list of names of the nodes
    :type n_list: str list

    :return: the list of Node objects
    :rtype: Node list
    """
    nodes = []
    if type(parent_node) is FileNode:
        for node in graph.successors(parent_node):
            for target_name in n_list:
                n_name = node.get_name()
                if n_name.endswith(target_name):
                    nodes.append(node)
    elif type(parent_node) is FolderNode:
        for node in graph.successors(parent_node):
            nodes += get_func_nodes(graph, node, n_list)
    return nodes


def imports_dict(graph):
    """
    Creates a dictionary of imported functions.

    :param graph: the tree representing the target code repo
    :type graph: networkx.MultiDiGraph

    :returns: A dictionary mapping the name of a Python file to a list of all modules it imports from its own repo, which is represented by `graph`.
    :rtype: dict {str : str list}
    """
    import_dict = {}
    node_visitor = ImportLister()

    for node in graph.nodes:
        if type(node) is FileNode:  # if at Python file
            node_visitor.visit(node.get_ast())

            imports = []
            for (name, level) in node_visitor.imported_mods:
                imported_node = get_repo_node(graph, node, name, level)
                if imported_node is not None:
                    funcs = node_visitor.imported_funcs[name]
                    imports += get_func_nodes(graph, imported_node, funcs)
            import_dict.update({node: imports})

            node_visitor.reset()

    return import_dict


def function_call_relationship(graph: nx.MultiDiGraph):
    """
    Creates a directed edge for when a module calls a function from another module
    from the target code repo.

    :param graph: the graph representing the target code repo
    :type graph: networkx.MultiDiGraph
    """
    import_dict = imports_dict(graph)
    node_visitor = CallLister()
    func_edges = []

    for node in graph.nodes:
        if type(node) is FileNode:
            node_visitor.visit(node.get_ast())

            for func in node_visitor.calls:
                for imported_func in import_dict[node]:
                    # get full function name as it would be called in code
                    n = imported_func.get_name().split(os.sep)[-1]
                    if n == func:
                        func_edges.append(
                            (node, imported_func, {'edge': edge.FunctionCallEdge("")}))

            node_visitor.reset()

    # add collected edges
    graph.add_edges_from(func_edges)


def inheritance_relationships(graph: nx.MultiDiGraph):
    """
    Creates a directed edge for whenever a class definition subclasses another class
    from the target code repo.

    :param graph: the graph representing the target code repo
    :type graph: networkx.MultiDiGraph
    """
    import_dict = imports_dict(graph)
    node_visitor = ClassLister()
    inherit_edges = []

    for node in graph.nodes:
        if type(node) is FileNode:  # if at Python file
            node_visitor.visit(node.get_ast())

            # get list of ClassNode objects corresponding to the class names
            classes = []
            for c in graph.successors(node):
                n = c.get_name().split(os.sep)[-1]
                if n in node_visitor.classes:
                    classes.append(c)

            for c in classes:
                # n1 is class name as it would appear in code
                n1 = c.get_name().split(os.sep)[-1]
                for imported_class in import_dict[node]:
                    # n2 is class name as it would appear in code
                    n2 = imported_class.get_name().split(os.sep)[-1]
                    # handle multiple inheritance later
                    extends = node_visitor.extends[n1]
                    if len(extends) == 1 and extends[0] == n2:
                        inherit_edges.append((c, imported_class,
                                              {'edge': edge.InheritanceEdge("")}))
                    for c2 in classes:
                        n3 = c2.get_name().split(os.sep)[-1]
                        if len(extends) == 1 and extends[0] == n3:
                            inherit_edges.append((c, c2,
                                                  {'edge': edge.InheritanceEdge("")}))

            node_visitor.reset()

    # add collected edges
    graph.add_edges_from(inherit_edges)


def definition_nodes(graph):
    """
    Adds ClassNode and FuncNode to the base `graph`.

    :param graph: the graph representing the target code repo
    :type graph: networkx.MultiDiGraph
    """
    node_visitor = DefinitionLister(graph)

    node_list = graph.nodes

    for node in node_list:
        if type(node) is FileNode:  # if at Python file
            node_visitor.starting_node = node
            node_visitor.visit(node.get_ast())
            # definitionLister already adds the edges

    return node_visitor.graph


def graph_to_string(graph: nx.MultiDiGraph, starting_node, level=0):
    """
    String representation of `graph` for debugging purposes.

    A class name is wrapped in brackets []. A function name is wrapped in parens ().
    For example, a graph 'g' representing Python module 'main.py' that defines
    function func1 and classes A and B, with A defining functions func2, func3:

    >>> graph_to_string(g, FileNode("main.py"))
    'main.py'
    '   (func1)'
    '   [A] (func2) (func3)'
    '   [B]'
    """
    abrev_name = str(starting_node).split(os.sep)[-1]
    if type(starting_node) is ClassNode:
        abrev_name = "[" + abrev_name + "]"
    elif type(starting_node) is FuncNode:
        abrev_name = "(" + abrev_name + ")"
    st = abrev_name
    level += 1
    for child in graph.successors(starting_node):
        # if children nodes arent class functions
        if not (type(child) is FuncNode and type(starting_node) is ClassNode):
            st += "\n" + " "*3*level + graph_to_string(graph, child, level)
        else:
            st += " " + graph_to_string(graph, child, level)

    return st


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
