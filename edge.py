"""
Module contains all the edge classes
"""
import Node
import networkx as nx

class DirectoryEdge():
    """
    Object that represents an edge in a graph 
    """

    def __init__(self, name):
        """
        Object initializer.

        :param name: name of the edge
        :type name: str
        """
        self.name = name

