"""
This module contains all the edge classes used by the generated graph. It should
be an edge attribute in the networkx module. 

>>> import networkx as nx
>>> import edge
>>> G = nx.Graph()
>>> G.add_edge("parent", "child", edge=DirectoryEdge("example"))
>>> G.add_edge("file", "import networkx", edge=ImportEdge("example"))
>>> G.add_edge("file", "funcion()", edge=FunctionCallEdge("example"))
>>> G.add_edge("classA", "classB", edge=InheritanceEdge("example"))
>>> G.add_edge("classA", "functionA", edge=DefinitionEdge("example"))
"""
import networkx as nx


class Edge():
    """
    Object that represents an edge in a graph. This is an abstract class.
    """

    def __init__(self, n):
        """
        Object initializer.

        :param name: name of the edge
        :type name: str
        """
        self.name = n

    def get_name(self):
        """
        Getter method for the name of the edge 

        :return: the name associated with the edge
        :rtype: str
        """
        return self.name


class DirectoryEdge(Edge):
    """
    This class represents an edge between two nodes, where one node is the parent
    directory of the other node (which is another directory or file).
    """

    def __init__(self, name):
        """
        Object initializer.

        :param name: name of the edge
        :type name: str
        """
        super().__init__(name)


class ImportEdge(Edge):
    """
    This class represents an edge between two nodes if one node imports a module
    from the other node.

    If a file contains an import statement, the node representing this import 
    will have an edge to the node representing the module. 
    """

    def __init__(self, name):
        """
        Object initializer.

        :param name: name of the edge
        :type name: str
        """
        super().__init__(name)


class FunctionCallEdge(Edge):
    """
    This class represets an edge betwee two nodes if one node represents a function
    call from another node.

    If a function is called within a file, the node that represents this in the 
    graph has an edge to the module containing the function.
    """

    def __init__(self, name):
        """
        Object initializer

        :param name: name of edge
        :type name: str
        """
        super().__init__(name)


class InheritanceEdge(Edge):
    """
    This class represents an edge between two nodes if one node inherits from 
    another node.

    If there is a class that inherits from another class, the node representing
    the subclass will have an edge to the super class. 
    """

    def __init__(self, name):
        """
        Object initializer

        :param name: name of edge
        :type name: str
        """
        super().__init__(name)


class DefinitionEdge(Edge):
    """
    This class represents an edge between two nodes if one node contains a
    definition that is contained within another node. 

    If a method is defined within a class, the node representing this method has
    an edge to the class where the method was defined. 
    """

    def __init__(self, name):
        """
        Object initializer

        :param name: name of edge
        :type name: str
        """
        super().__init__(name)


class VariableEdge(Edge):
    """
    A VariableEdge from Node ``u`` to Node ``v`` represents: 
    "``u`` uses variable ``v``"
    """

    def __init__(self, name):
        """
        Object initializer

        :param name: name of edge
        :type name: str
        """
        super().__init__(name)


class ControlFlowEdge(Edge):
    """
    A ControlFlowEdge from Node ``u`` to Node ``v`` represents the control flow
    of the program.
    """

    def __init__(self, name):
        """
        Object initializer

        :param name: name of edge
        :type name: str
        """
        super().__init__(name)
