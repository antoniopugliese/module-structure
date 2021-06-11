"""
Node module comment
"""

from abc import ABC, abstractmethod


class Node(ABC):
    """
    This abstract Node class is extended to build a tree that represents a software 
    module. The Node subclasses represent either a folder or Python file. 
    """
    # "Hashable objects which compare equal must have the same hash value."
    # Node() names are unique, since they are complete file paths. Need to have
    # warnings (or prevent) users from attempting to add Nodes with same name.

    def __eq__(self, value):
        return self.name == value.name

    def __hash__(self):
        return id(self.name)

    def __str__(self):
        return self.name

    def __init__(self, n):
        """
        Initializes the Node object.

        :param n: name of the instance (file or directory) 
        :type n: str

        :return: A Node object containing n and p.
        :rtype: Node
        """
        self.name = n

    def to_string(self):
        return self.name

    def get_name(self):
        """
        Getter method to return the name of the Node.

        :return: name of Node
        :rtype: str
        """
        return self.name


class FolderNode(Node):
    """
    The Node subclass that represents a directory. It contains a ``children``
    attribute that stores its child Nodes, which may be files or other directories.
    """

    def __init__(self, n):
        """
        Initializes the FolderNode.

        :param n: the full filepath name of the directory.
        :type n: str

        :param p: the name of the parent directory, None if this directory is root folder.
        :type p: str

        :return: A FolderNode object containing `n`.
        :rtype: FolderNode

        >>> FolderNode('C:\\Users\\Jackson\\Documents\\example')
        """
        super().__init__(n)


class FileNode(Node):
    """
    The Node subclass that represents a Python file. It contains a ``tree``
    attribute that stores the abstract syntax tree (AST) of the Python file it
    represents. A FileNode cannot have any children Nodes (it must be a leaf).
    """

    def __init__(self, n, ast):
        """
        Initializes the FileNode with the AST of the Python file given by `n`.

        :param n: the full filepath name of the Python file.
        :type n: str

        :param ast: the AST of the Python file.
        :type ast: ast

        :return: A FileNode object containing `n`, `p`, and `ast`.
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
