"""
This module constructs a networkx subgraph according to a user's selection of node and
edge types.

>>> import subgraph as sg
>>> g.nodes
    [FolderNode('root'), FileNode('main.py'), FolderNode('src')]
>>> h = sg.subgraph(g, ["Folder"], [])
>>> h.nodes
    [FolderNode('root'), FolderNode('src')]
"""

import networkx as nx
import os
import node
import edge
import json

# List of possible nodes
NODES = {
    "Folder": node.FolderNode,
    "File": node.FileNode,
    "Class": node.ClassNode,
    "Function": node.FuncNode,
    "Variable": node.VarNode,
    "Lambda": node.LambdaNode,
    "If": node.IfNode,
    "For": node.ForNode,
    "While": node.WhileNode,
    "Try": node.TryNode,
}

# List of possible edges
EDGES = {
    "Directory": edge.DirectoryEdge,
    "Import": edge.ImportEdge,
    "Function Call": edge.FunctionCallEdge,
    "Inheritance": edge.InheritanceEdge,
    "Definition": edge.DefinitionEdge
}

def get_preferences():
    """
    Finds and retrieves preferences from the ``config`` file.

    :return: a tuple of lists: the first is the list of Nodes to include, and the second is the list of Edges to include.
    :rtype: (str list, str list)

    >>> get_preferences()
    (['Folder', 'File'], ['Directory'])
    """
    # potentially use path finding function from parsing.py
    current_dir = os.path.dirname(os.path.abspath(__file__))

    with open(os.path.join(current_dir, "config.json"), "r") as f:
        config = json.load(f)

    return (config["nodes"], config["edges"])


def str_to_node(str):
    """
    Converts a string to type node.Node.

    :param str: a string representing a node in node.py
    :type str: str

    :return: a node.Node object
    :rtype: node.Node

    >>> str_to_node("Folder")
    node.FolderNode
    """
    try:
        return NODES.get(str)
    except KeyError:
        raise ValueError(f"Node must be one of {NODES}")


def str_to_edge(str):
    """
    Converts a string to type edge.Edge.

    :param str: a string representing an edge in edge.py
    :type str: str

    :return: a edge.Edge object
    :rtype: edge.Edge

    >>> str_to_edge("Directory")
    edge.DirectoryEdge
    """
    try:
        return EDGES.get(str)
    except KeyError:
        raise ValueError(f"Edge must be one of {EDGES}")


def subgraph(graph: nx.MultiDiGraph, nodes, edges):
    """
    Creates a subgraph of the given graph based on user preferences.

    :param graph: the graph used to make the subgraph
    :type graph: networkx.MultiDiGraph

    :param nodes: the list of node types to include
    :type nodes: str list

    :param edges: the list of edge types to include
    :type edges: str list

    :return: the subgraph of ``graph`` with the chosen edge and node types included
    :rtype: nx.MultiDiGraph

    >>> g.nodes
    [FolderNode('root'), FileNode('main.py'), FolderNode('src')]
    >>> h = subgraph(g, ["Folder"], [])
    >>> h.nodes
    [FolderNode('root'), FolderNode('src')]
    """
    subgraph = nx.MultiDiGraph()

    node_list = list(map(str_to_node, nodes))
    edge_list = list(map(str_to_edge, edges))

    # generate a list nodes in the subgraph
    sub_nodes = [(n, d)
                 for n, d in graph.nodes(data=True) if type(n) in node_list]

    # generate a list edges in the subgraph
    sub_edges = [(start, end, edge_attribute)
                 for start, end, edge_attribute in graph.edges(data=True)
                 if (type(edge_attribute['edge']) in edge_list)]

    # add all nodes and edges to the graph
    subgraph.add_nodes_from(sub_nodes)
    subgraph.add_edges_from(sub_edges)

    # remove nodes not to be included
    removes = [n for n in subgraph.nodes if type(n) not in node_list]
    subgraph.remove_nodes_from(removes)

    return subgraph

