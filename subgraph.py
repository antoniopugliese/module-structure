"""
This module will be used for subgraphing.
"""
import networkx as nx
import os
import node
import edge
import json


def get_preferences():
    """
    Finds and retrieves preferences from the ``config`` file.

    :return: a tuple of lists: the first is the list of Nodes to include, and 
    the second is the list of Edges to include.
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
    """
    nodes = {
        "Folder" : node.FolderNode,
        "File" : node.FileNode, 
        "Class" : node.ClassNode,
        "Function" : node.FuncNode
    }
    return nodes.get(str, "Invalid node in config")

def str_to_edge(str):
    """
    Converts a string to type edge.Edge

    :param str: a string representing an edge in edge.py
    :type str: str

    :return: a edge.Edge object
    :rtype: edge.Edge
    """
    edges = {
        "Directory" : edge.DirectoryEdge,
        "Import" : edge.ImportEdge,
        "Function_call" : edge.ImportEdge,
        "Inheritance" : edge.InheritanceEdge,
        "Definition" : edge.DefinitionEdge
    }
    return edges.get(str, "Invalid edge in config")

def subgraph(graph: nx.MultiDiGraph):
    """
    Creates a subgraph of the given graph based on user preferences in the ``config`` file.

    :param graph: the graph to make the subgraph
    :type graph: networkx.MultiDiGraph

    :return: the subgraph of ``graph`` with the chosen edge and node types included
    :rtype: nx.MultiDiGraph
    >>> g.nodes
    [FolderNode('root'), FileNode('main.py'), FolderNode('src')]
    >>> config["nodes"]
    ["Folder"]
    >>> h = subgraph(g)
    >>> h.nodes
    [FolderNode('root'), FolderNode('src')]
    """
    nodes, edges = get_preferences()
    subgraph = nx.MultiDiGraph()

    node_list = map(str_to_node, nodes)
    edge_list = map(str_to_edge, edges)

    for n, d in graph.nodes.data():
        # conditional for whether node should be added. Short circuit evaluation should
        # make this more efficient.
        # should_include = ("Folder" in nodes and type(n) is node.FolderNode) or (
        #     "File" in nodes and type(n) is node.FileNode) or (
        #     "Class" in nodes and type(n) is node.ClassNode) or (
        #     "Function" in nodes and type(n) is node.FuncNode)
        # if should_include:
        #     subgraph.add_node(n, *d)
        if type(n) in node_list:
            subgraph.add_node(n, *d)

    eligible_edges = [(start, end, edge_attribute)  
    	for start, end, edge_attribute in subgraph.edges(data=True) 
	    if type(edge_attribute['edge']) in edge_list]

    subgraph.add_edges_from(eligible_edges)

    return subgraph
