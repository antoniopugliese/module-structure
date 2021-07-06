"""
This module defines node objects to be used in constructing a graph representing
the file structure of a code repo, and the structure of its Python code files.
"""

from abc import ABC


class Node(ABC):
    """
    This abstract Node class is extended to build a tree that represents a software 
    module. The Node subclasses represent a folder, Python file, Python class, or
    Python function. 
    """
    # "Hashable objects which compare equal must have the same hash value."
    # Node() names are unique, since they are complete file paths. Need to have
    # warnings (or prevent) users from attempting to add Nodes with same name.

    def __eq__(self, value):
        """
        Two Node objects are defined to be equal if they have the same name. Since node 
        names are full filepaths, these names will be unique for each folder or
        file they represent.
        """
        return self.name == value.name

    def __hash__(self):
        """
        The hash of the string name of the Node object.
        """
        # id(self.name) changes each time the program is run, which prevents
        # the pickled graph from being used, so the hash of the name is used instead
        return self.name.__hash__()

    def __str__(self):
        """
        The string representation of a Node object is its name.
        """
        return self.name

    def __init__(self, n):
        """
        Initializes the Node object.

        :param n: name of the instance (file or directory) 
        :type n: str

        :return: A Node object containing n.
        :rtype: Node
        """
        self.name = n

    def get_name(self):
        """
        Getter method to return the name of the Node.

        :return: name of Node
        :rtype: str
        """
        return self.name


class FolderNode(Node):
    """
    The Node subclass that represents a directory. In a graph, this Node will have
    children nodes, and at most one parent Node.
    """

    def __init__(self, n):
        """
        Initializes the FolderNode.

        :param n: the full filepath name of the directory.
        :type n: str

        :return: A FolderNode object containing `n`.
        :rtype: FolderNode

        >>> FolderNode('C:\\Users\\Jackson\\Documents\\example')
        """
        super().__init__(n)


class FileNode(Node):
    """
    The Node subclass that represents a Python file. It contains a ``tree``
    attribute that stores the abstract syntax tree (AST) of the Python file it
    represents. A FileNode cannot have any FolderNode or FileNode children nodes,
    but may have ClassNode or FuncNode children nodes.
    """

    def __init__(self, n, ast):
        """
        Initializes the FileNode with the AST of the Python file given by `n`.

        :param n: the full filepath name of the Python file.
        :type n: str

        :param ast: the AST of the Python file.
        :type ast: ast

        :return: A FileNode object containing `n` and `ast`.
        :rtype: FileNode

        >>> FileNode('C:\\Users\\Jackson\\Documents\\example\\main.py', ast)
        """
        super().__init__(n)
        self.tree = ast

    def get_ast(self):
        """
        Getter method to return the abstract syntax tree of the file.

        :return: AST of file 
        :rtype: ast
        """
        return self.tree


class ClassNode(Node):
    """
    The Node subclass that represents a class defined within a Python file. 
    A ClassNode object must be a child node of a FileNode object, and can only
    have ClassNode or FuncNode objects as children nodes.
    """

    def __init__(self, n, ast):
        """
        Initializes ClassNode object.

        :param n: the full filepath name of the Python file, and the name of the class.
        :type n: str

        :param ast: the AST of the class.
        :type ast: ast

        :return: A ClassNode object containing `n` and `ast`.
        :rtype: ClassNode

        For ``class A`` defined within Python file 'main.py' with AST 'ast':
        >>> ClassNode('C:\\Users\\Jackson\\Documents\\example\\main.py\\A', ast)
        """
        super().__init__(n)
        self.tree = ast


class FuncNode(Node):
    """
    The Node subclass that represents a function defined within a Python file or
    a Python class. 
    """

    def __init__(self, n, ast):
        """
        Initializes FuncNode object.

        :param n: the full function name.
        :type n: str

        :param ast: the AST object representing a function
        :type ast: ast.FunctionDef

        For function ``func_a()`` defined within Python file 'main.py' with AST 'ast':
        >>> ClassNode('C:\\Users\\Jackson\\Documents\\example\\main.py\\func_a', ast)
        """
        super().__init__(n)
        self.tree = ast


class VarNode(Node):
    """
    The Node subclass that represents a variable defined within a Python file,
    Python class, or Python function.
    """

    def __init__(self, n, ast):
        """
        Initializes VarNode object.

        :param n: the full variable name.
        :type n: str

        :param ast: the AST object representing a variable.
        :type ast: ast.VariableDef
        """
        super().__init__(n)
        self.tree = ast


class LambdaNode(Node):
    """
    The Node subclass that represents a Python lambda function.
    """

    def __init__(self, n, ast):
        """
        Initializes LambdaNode object.

        :param ast: the AST object representing a Lambda expression.
        :type ast: ast.Lambda

        :return: A LambdaNode object containing `n` and `ast`.
        :rtype: LambdaNode 
        """
        super().__init__(n)
        self.tree = ast


class IfNode(Node):
    """
    The Node subclass that represents a Python ``if`` statement.
    """


class ForNode(Node):
    """
    The Node subclass that represents a Python ``for`` loop. 
    """

    def __init__(self, n):
        """
        Initializes a ForNode

        :param n: the name of the for loop.
        :type n: str
        """
        super().__init__(n)
