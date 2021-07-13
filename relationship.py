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
from node import (FileNode, FolderNode, ClassNode, FuncNode,
                  VarNode, LambdaNode, ForNode, IfNode, WhileNode, TryNode)
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

    def visit_Import(self, node: ast.Import):
        """
        Gathers all the imported modules. 

        :param node: the node that represents an import
        :type node: ast.Import
        """
        for alias in node.names:
            self.imported_mods.append((alias.name, 1))

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


class NodeMaker(ast.NodeVisitor):
    """
    This class will gather classes, functions, and variables defined within an AST, and add
    Node object representations of them to an existing root.
    """

    def __init__(self, root):
        """
        The root to add the ClassNode, FuncNode, and VarNode.

        :param root: the FileNode object corresponding to the Python file of the AST.
        :type root: Node
        """
        super().__init__()
        # copy the graph to make sure original data is preserved
        self.graph = nx.MultiDiGraph()
        self.graph.add_edges_from(root.edges.data())
        self.starting_node = None

    def change_scope(self, new, node):
        """
        Temporarily changes the scope to visit the children of a AST node. 

        :param new: new starting node
        :type new: Node

        :param node: current node that is being visited
        :type node: Node
        """
        temp = self.starting_node
        self.starting_node = new
        self.generic_visit(node)
        self.starting_node = temp

    def visit_ClassDef(self, node):
        """
        Adds a ClassNode to the graph, as well as any functions defined in the class.

        :param node: a node that represents a class definition
        :type node: ast.ClassDef
        """
        class_name = os.path.join(self.starting_node.name, node.name)
        class_node = ClassNode(class_name, node)
        # edge (u,v): "u defines v"
        self.graph.add_edge(self.starting_node, class_node,
                            edge=edge.DefinitionEdge(""))

        # Add FuncNodes as children of this ClassNode
        self.change_scope(class_node, node)

    def visit_FunctionDef(self, node):
        """
        Adds a FuncNode to the graph.

        :param node: a node representing the function definition.
        :type node: ast.FunctionDef
        """
        func_name = os.path.join(self.starting_node.name, node.name)
        func_node = FuncNode(func_name, node)

        # edge (u,v): "u defines v"
        self.graph.add_edge(self.starting_node, func_node,
                            edge=edge.DefinitionEdge(""))

        # Add VarNodes as children of this FuncNode
        self.change_scope(func_node, node)

    def visit_Assign(self, node: ast.Assign):
        """
        Adds a VarNode and creates a DefinitionEdge between the function,
        class, or file that defined the variable.
        """
        for name in node.targets:
            if type(name) is ast.Name:
                var_name = os.path.join(self.starting_node.name, name.id)
                var_node = VarNode(var_name, node.value)
                if type(name.ctx) is ast.Store:
                    # edge (u,v): "u defines variable v"
                    self.graph.add_edge(self.starting_node, var_node,
                                        edge=edge.DefinitionEdge(""))

                    # See if other nodes are used in this variable assignment
                    self.change_scope(var_node, node)

    def visit_Name(self, node: ast.Name):
        """
        Draws a VariableEdge between the function, class, or file that uses a 
        variable.

        :param node: a node representing the variable.
        :type node: ast.Name
        """
        if type(node.ctx) is ast.Load:
            var_name = node.id

            current_path = self.starting_node.get_name()
            i = len(current_path.split(os.sep))

            # hueristic to look through scopes to try and find variable declaration
            while i > 0:
                path = current_path.split(os.sep)[:i]
                var_node = VarNode(os.path.join(*path, var_name), None)
                if self.graph.has_node(var_node):
                    # edge (u,v): "variable u is used in v"
                    self.graph.add_edge(var_node, self.starting_node,
                                        edge=edge.VariableEdge(""))
                    break
                # stop search after searching through entire file scope
                if path[-1].endswith(".py"):
                    break
                i -= 1

    def visit_Lambda(self, node: ast.Lambda):
        """
        Adds a LambdaNode to the graph and draws a DefinitionEdge.

        :param node: the ast node representing the lambda.
        :type node: ast.Lambda
        """
        base = self.starting_node.name
        i = 1
        lambda_node = LambdaNode(os.path.join(base, "lambda1"), node.body)

        # might be multiple lambdas in this scope
        while self.graph.has_node(lambda_node):
            i += 1
            lamb = "lambda" + str(i)
            lambda_node = LambdaNode(os.path.join(base, lamb), node.body)

        # edge (u,v): "u defines lambda v"
        self.graph.add_edge(self.starting_node, lambda_node,
                            edge=edge.DefinitionEdge(""))

    def visit_For(self, node: ast.For):
        """
        Adds a ForNode to the graph and draws a DefinitionEdge. Draws a
        VariableEdge if a variable is used in the test clause. Draws ControlFlowEdge
        between variables that are modified within the for loop.

        :param node: the ast node representing the for loop.
        :type node: ast.For
        """
        base = self.starting_node.name
        i = 1
        for_node = ForNode(os.path.join(base, "for1"))

        # might be multiple for loops in this scope
        while self.graph.has_node(for_node):
            i += 1
            for_st = "for" + str(i)
            for_node = ForNode(os.path.join(base, for_st))

        # edge (u,v): "u defines for loop v"
        self.graph.add_edge(self.starting_node, for_node,
                            edge=edge.DefinitionEdge(""))

        # TODO: node.iter - draw VariableEdge to variable being looped over.

        # TODO: node.body - draw ControlFlowEdge if modifies some variable

        # TODO: node.orelse - rare else statement in for loops

        # self.change_scope(for_node, node)
        self.generic_visit(node)

    def visit_While(self, node: ast.While):
        """
        Adds a WhileNode to the graph and draws a DefinitionEdge. Draws a
        VariableEdge if a variable is used in the test clause. Draws ControlFlowEdge
        between variables that are modified within the while loop.

        :param node: the ast node representing the while loop.
        :type node: ast.While
        """
        base = self.starting_node.name
        i = 1
        while_node = WhileNode(os.path.join(base, "while1"))

        # might be multiple while loops in this scope
        while self.graph.has_node(while_node):
            i += 1
            while_st = "while" + str(i)
            while_node = WhileNode(os.path.join(base, while_st))

        # edge (u,v): "u defines while loop v"
        self.graph.add_edge(self.starting_node, while_node,
                            edge=edge.DefinitionEdge(""))

        # node.test - draw VariableEdge if depends on some variable
        self.change_scope(while_node, node.test)

        # TODO: node.body - draw ControlFlowEdge if modifies some variable

        # TODO: node.orelse - rare else statement in while loops.

        # self.change_scope(while_node, node)
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try):
        """
        Adds a TryNode to the graph and draws a DefinitionEdge. Draws ControlFlowEdge
        between variables that are modified within the try statement.

        :param node: the ast node representing the try statement.
        :type node: ast.Try
        """
        base = self.starting_node.name
        i = 1
        try_node = TryNode(os.path.join(base, "try1"))

        # might be multiple while loops in this scope
        while self.graph.has_node(try_node):
            i += 1
            try_st = "try" + str(i)
            try_node = WhileNode(os.path.join(base, try_st))

        # edge (u,v): "u defines while loop v"
        self.graph.add_edge(self.starting_node, try_node,
                            edge=edge.DefinitionEdge(""))

        # TODO: node.body - draw ControlFlowEdge if modifies some variable

        #self.change_scope(try_node, node)
        self.generic_visit(node)

    def visit_If(self, node: ast.If):
        """
        Adds a IfNode to the graph and draws a DefinitionEdge. Draws a
        VariableEdge if a variable is used in the test clause. Draws ControlFlowEdge
        between variables that are modified within the if statement.

        :param node: the ast node representing the if statement.
        :type node: ast.If
        """
        base = self.starting_node.name
        i = 1
        if_node = IfNode(os.path.join(base, "if1"))

        # might be multiple if statements in this scope
        while self.graph.has_node(if_node):
            i += 1
            if_st = "if" + str(i)
            if_node = IfNode(os.path.join(base, if_st))

        # edge (u,v): "u defines if statement v"
        self.graph.add_edge(self.starting_node, if_node,
                            edge=edge.DefinitionEdge(""))

        # node.test - draw VariableEdge if depends on some variable
        self.change_scope(if_node, node.test)

        # TODO: node.body - draw ControlFlowEdge if modifies some variable
        for child in node.body:
            # walk child nodes to create loop variables
            self.change_scope(if_node, child)

        # TODO: node.orelse - draw ControlFlowEdge if modifies some var;
        # check for nested if statements
        for child in node.orelse:
            # walk child nodes to create loop variables
            self.change_scope(if_node, child)

        self.change_scope(if_node, node)
        # self.generic_visit(node)


def get_repo_node_helper(graph, starting_node, mod, level):
    """
    Helper for get_repo_node which searches for relative imports.

    :param graph: the graph representing the target repo
    :type graph: networkx.MultiDiGraph

    :param starting_node: the name of the node to start the search from
    :type starting_node: str

    :param mod: the name of the target Python module
    :type mod: str

    :param level: the level of the relative import (level=0 means an absolute import)
    :type level: int

    :return: FileNode object associated with ``mod``
    :rtype: FileNode
    """
    # print(f"relative for {mod}")
    # for relative imports, go up in directories according to level
    target_node = starting_node
    while (level != 0):
        # each node only has one direct predeccesor
        target_node = list(graph.predecessors(target_node))[0]
        level -= 1

    # after reaching top directory, search successors recursively for target
    for node, succesors in nx.bfs_successors(graph, target_node):
        # need to match last parts of each node name exactly

        # -index is the number of parts to match with. for example, to search for
        # mod 'apply.core', we need to match [apply], [core] (or [apply], [core.py])
        index = -len(mod.split("."))

        # get the last parts of the current node
        n = node.get_name().split(os.sep)[index:]

        # make folder and file version of module. Ex. the folder apply/core or the
        # file apply/core.py
        mod_folder = mod.split(".")[index:]
        mod_file = mod.split(".")[index:-1] + \
            [(mod.split(".")[-1] + ".py")]

        if n == mod_folder or n == (mod_file):
            return node
    return None


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

    :return: FileNode object associated with ``mod``
    :rtype: FileNode
    """
    if level == 0:
        # for absolute imports, search to see if module in graph
        target_node_name = mod.replace('.', os.sep)
        for node in graph.nodes:
            n = node.get_name()
            if n.endswith(target_node_name) or n.endswith(target_node_name + ".py"):
                return node
        return None
    else:
        return get_repo_node_helper(graph, starting_node, mod, level)


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
                    # edge (u,v): "u is imported by v"
                    imports.append((imported_node, node, {
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

    :returns: A dictionary mapping the name of a Python file to a list of all 
    modules it imports from its own repo, which is represented by `graph`.
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
                    try:
                        funcs = node_visitor.imported_funcs[name]
                        imports += get_func_nodes(graph, imported_node, funcs)
                    except KeyError:
                        pass  # Import statements do not have associated functions
                        # like ImportFrom statements

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
                        # edge (u,v): "u is called by v"
                        func_edges.append(
                            (imported_func, node, {'edge': edge.FunctionCallEdge("")}))

            node_visitor.reset()

    # add collected edges
    graph.add_edges_from(func_edges)


def inheritance_relationship_class_helper(graph, node, node_visitor):
    """
    Helper for inheritance_relationship() that generates a list of ClassNode objects.

    :param graph: the graph representing the target code repo
    :type graph: networkx.MultiDiGraph

    :param node: the current node in the graph
    :type node: networkx.node

    :param node_visitor: the type of nodes that are visited
    :type node_visitor: ClassLister()

    :return: a list of nodes representing the classes in the repo
    :rtype: node.Node list
    """
    classes = []

    for c in graph.successors(node):
        n = c.get_name().split(os.sep)[-1]
        if n in node_visitor.classes:
            classes.append(c)

    return classes


def inheritance_relationship_import_helper(classes, node, import_dict, node_visitor, inherit_edges):
    """
    Helper method for inheritance_relationship() that determines every inheritance
    in the file structure.

    :param classes: a list of nodes representing the classes in the repo
    :type classes: node.Node list

    :param node: the current node in the graph
    :type node: networkx.node

    :param import_dict: a dictionary of all imported functions
    :type import_dict: {str : str list} 

    :param node_visitor: the type of nodes that are visited
    :type node_visitor: ClassLister()

    :param inherit_edges: list of inheritances in the file structure
    :type inherit_edges: str list 
    """
    for c in classes:
        # n1 is class name as it would appear in code
        n1 = c.get_name().split(os.sep)[-1]
        for imported_class in import_dict[node]:
            # n2 is class name as it would appear in code
            n2 = imported_class.get_name().split(os.sep)[-1]
            # handle multiple inheritance later
            extends = node_visitor.extends[n1]
            if len(extends) == 1 and extends[0] == n2:
                # edge (u,v): "u is a parent class of v"
                new_edge = (imported_class, c, {'edge': edge.InheritanceEdge("")}) 
                if new_edge not in inherit_edges:
                    inherit_edges.append(new_edge)
            for c2 in classes:
                n3 = c2.get_name().split(os.sep)[-1]
                if len(extends) == 1 and extends[0] == n3:
                    # edge (u,v): "u is a parent class of v"
                    new_edge = (c2, c, {'edge': edge.InheritanceEdge("")}) 
                    if new_edge not in inherit_edges:
                        inherit_edges.append(new_edge)


def inheritance_relationship(graph: nx.MultiDiGraph):
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
            classes = inheritance_relationship_class_helper(
                graph, node, node_visitor)

            # get all inheritances
            inheritance_relationship_import_helper(
                classes, node, import_dict, node_visitor, inherit_edges)

            node_visitor.reset()

    # add collected edges
    graph.add_edges_from(inherit_edges)


def add_graph_nodes(graph):
    """
    Adds ClassNode, FuncNode, and VarNode to the base ``graph``.

    :param graph: the graph representing the target code repo
    :type graph: networkx.MultiDiGraph
    """
    node_visitor = NodeMaker(graph)

    for node in graph.nodes:
        if type(node) is FileNode:  # if at Python file
            node_visitor.starting_node = node
            node_visitor.visit(node.get_ast())
            # definitionLister already adds the edges

    return node_visitor.graph


def create_all_relationships(graph):
    """
    Adds all available relationship edges and nodes to ``graph``.

    :param graph: the graph to add the relationships to.
    :type graph: networkx.MultiDiGraph

    :return: the graph with all relationships added
    :rtype: networkx.MultiDiGraph
    """
    new_graph = add_graph_nodes(graph)
    import_relationship(new_graph)
    function_call_relationship(new_graph)
    inheritance_relationship(new_graph)

    return new_graph


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
    elif type(starting_node) is VarNode:
        abrev_name = "$" + abrev_name + "$"
    st = abrev_name
    level += 1
    if not (type(starting_node) is VarNode):
        for child in graph.successors(starting_node):
            # if children nodes arent class functions
            if (type(child) is FuncNode and type(starting_node) is ClassNode):
                st += " " + graph_to_string(graph, child, level)
            else:
                st += "\n" + " "*3*level + graph_to_string(graph, child, level)

    return st
