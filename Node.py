from abc import ABC, abstractmethod


class Node(ABC):
    """
    This abstract Node class is extended to build a tree that represents a software 
    module. The Node subclasses represent either a folder or Python file. 
    """

    def __init__(self, n, p):
        """
        Initializes the Node object.

        :param n: name of the instance (file or directory) 
        :type n: str

        :param p: the name of the parent of the Node object, None if doesn't exist
        :type p: str

        :return: A Node object containing n and p.
        :rtype: Node
        """
        self.name = n
        self.parent = p

    @abstractmethod
    def to_string(self, level=0):
        pass

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

    def __init__(self, n, p):
        """
        Initializes the FolderNode with no children Nodes.

        :param n: name of the directory.
        :type n: str

        :param p: the name of the parent directory, None if this directory is root folder.
        :type p: str

        :return: A FolderNode object containing `n` and `p`.
        :rtype: FolderNode

        >>> FolderNode('example', None)
        >>> FolderNode('child', 'example')
        """
        super().__init__(n, p)
        self.children = []

    def add_child(self, child):
        """
        Adds a child to the FolderNode object. 

        :param child: Node object to add to the FolderNode. 
        :type child: Node

        :return: FolderNode object with child added to its list of children.
        :rtype: FolderNode 

        >>> example = FolderNode('example', None)
        >>> example.add_child(FolderNode('child_1', 'example'))
        >>> example.add_child(FolderNode('child_2', 'example'))
        >>> example.children
        [FolderNode('child_1', 'example'), FolderNode('child_2', 'example')]
        """
        self.children.append(child)

    def to_string(self, level=0):
        """
        The string representation of the FolderNode and all of its children Nodes.
        Mainly intended for debugging purposes.

        :param level: the current depth of the Node, defaults to 0.
        :type level: int

        :return: A string representing the FolderNode and all its children.
        :rtype: str

        >>> example = FolderNode('src', None)
        >>> example.to_string()
        'src'

        >>> example.add_child(FolderNode('child', 'src'))
        >>> example.add_child(FileNode('code.py', 'src', 'ast'))
        >>> example.to_string()
        'src'
            'child'
            'code.py'
        """
        base = self.name + "\n"
        level += 1
        for child in self.children:
            base += " "*4*level + child.to_string(level)
        return base

    def get_children(self):
        """
        Getter method for the children of the Node

        :return: the list of children from the Node
        :rtype: Node list
        """
        return self.children


class FileNode(Node):
    """
    The Node subclass that represents a Python file. It contains a ``tree``
    attribute that stores the abstract syntax tree (AST) of the Python file it
    represents. A FileNode cannot have any children Nodes (it must be a leaf).
    """

    def __init__(self, n, p, ast):
        """
        Initializes the FileNode with the AST of the Python file given by `n`.

        :param n: name of the Python file.
        :type n: str

        :param p: the name of the parent directory, if any.
        :type p: str

        :param ast: the AST of the Python file.
        :type ast: ast

        :return: A FileNode object containing `n`, `p`, and `ast`.
        :rtype: FileNode
        """
        super().__init__(n, p)
        self.tree = ast

    def to_string(self, level=0):
        """
        The string representation of the FileNode. Mainly intended for debugging purposes.

        :param level: the current depth of the Node, defaults to 0.
        :type level: int

        :return: the name of the Python file.
        :rtype: str

        >>> FileNode("code.py","root","ast").to_string()
        'code.py'
        """
        return self.name + "\n"

    def get_ast(self):
        """
        Getter method to return the abstract syntax tree of the file.

        :return: AST of file 
        :rtype: ast
        """
        return self.tree


def traversal(root):
    """
    Traverses the tree using a breadth-first-search approach. 

    :param root: the root of the tree 
    :type root: Node

    :return: list of all the Nodes in the tree
    :rtype: Node list
    """
    if root is None:
        return []

    visited = [root]
    queue = [root]

    while queue:
        curr_node = queue.pop(0)

        if type(curr_node) is FileNode:
            if curr_node not in visited:
                visited.append(curr_node)
        else:
            for child in curr_node.get_children():
                if child not in visited:
                    visited.append(child)
                    queue.append(child)

    return visited


def find_name(root, n):
    """
    Finds a Node with name n in a tree starting at the root. 

    :param root: the root of the tree
    :type root: Node

    :param n: the name of the Node
    :type n: str

    :return: the Node with name n, None if not found
    :rtype: Node
    """
    if root is None:
        return None

    visited = [root.get_name()]
    queue = [root]

    while queue:
        curr_node = queue.pop(0)
        curr_name = curr_node.get_name()

        if curr_name == n:
            return curr_node

        if type(curr_node) is FolderNode:
            if curr_node not in visited:
                for child in curr_node.get_children():
                    visited.append(child.get_name())
                    queue.append(child)
        else:
            continue

    return None


def find_ast(root, n):
    """
    Finds the abstract syntax tree of file with name `n` in a tree starting at 
    root. If the file cannot be found, return None.

    :param root: the root of the tree
    :type root: Node

    :param n: the name of the file
    :type n: str

    :return: the ast of file n
    :rtype: ast.Module
    """
    node = find_name(root, n)

    if node is None or type(node) is FolderNode:
        return None

    return node.get_ast()
