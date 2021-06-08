"""
This module contains all the edge classes used by the generated graph. 
"""
import Node
import networkx as nx


class Edge():
    """
    Object that represents an edge in a graph. 
    """
    def __init__(self, name):
        """
        Object initializer.

        :param name: name of the edge
        :type name: str
        """
        self.name = name
    
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
    directory of the other node. 
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
    """
    def __init__(self, name):
        """
        Object initializer.

        :param name: name of the edge
        :type name: str
        """
        super().__init__(name)