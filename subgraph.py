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

    for n, d in graph.nodes.data():
        # conditional for whether node should be added. Short circuit evaluation should
        # make this more efficient.
        should_include = ("Folder" in nodes and type(n) is node.FolderNode) or (
            "File" in nodes and type(n) is node.FileNode) or (
            "Class" in nodes and type(n) is node.ClassNode) or (
            "Function" in nodes and type(n) is node.FuncNode)

        if should_include:
            subgraph.add_node(n, *d)

    return subgraph
