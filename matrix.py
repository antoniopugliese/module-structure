"""
This module will take in a NetworkX graph and construct an adjacency matrix from
this graph.
"""
import networkx as nx
import networkx.linalg.laplacianmatrix as laplac
import scipy as sp
# import scipy.linalg as linalg
import scipy.sparse.linalg as linalg
import numpy as np

MATRIX = {
    "adjacency": nx.adjacency_matrix,
    ### the following are 'not implemented' for MultiDiGraphs. ###
    "laplacian": laplac.laplacian_matrix,
    "normalized": laplac.normalized_laplacian_matrix,
    "directed": laplac.directed_laplacian_matrix,
    "combinatorial": laplac.directed_combinatorial_laplacian_matrix
}


def graph_to_matrix(graph, order=None, weight=None, matrix="adjacency"):
    """
    Converts a NetworkX graph into an adjacency matrix.

    :param graph: a NetworkX graph
    :type graph: NetworkX graphh

    :param order: a list or ordered nodes in the NetworkX graph
    :type order: Node list

    :param weight: represents which weight will be represented in the matrix
    :type weight: int

    :param matrix: the type of matrix wanted
    :type matrix: str

    :return: a sparse matrix representation of the graph
    :rtype: scipy.sparse
    """
    # if matrix == "adjacency":
    #     return nx.adjacency_matrix(graph, order, weight)
    # elif matrix == "laplacian":
    #     return nx.laplacian_matrix(graph, order, weight)
    # elif matrix == "normalized":
    #     return nx.normalized_laplacian_matrix(graph, order, weight)
    # elif matrix == "directed":
    #     return nx.directed_laplacian_matrix(graph, order, weight)
    # elif matrix == "combinatorial":
    #     return nx.directed_combinatorial_laplacian_matrix(graph, order, weight)
    func = MATRIX.get(matrix)  # exception for invalid type
    return func(graph, order, weight)


# scipy.linalg does not support sparse matricies
# scipy.sparse.linalg does support, but cannot calculate all eigenvalues
SPECTRUM = {
    "eigenvalue": linalg.eigen.eigs,
    "svd": linalg.eigen.svds
}


def analyze_matrix(matrix, type="eigenvalue"):
    """
    Calculates the singular values or eigenvalues from a matrix.

    :param matrix: a sparse matrix representing a NetworkX graph
    :type matrix: scipy.sparse

    :param type: either singular values or eigenvalues
    :type type: str

    :return: a unitary matrix
    :rtype: ndarray
    """
    # matrix elements need to be 'upgraded' before analyzed
    matrix = matrix.asfptype()
    # the dimension of the square matrix
    dim = matrix.shape[0]
    func = SPECTRUM.get(type)
    return func(matrix, k=dim - 2)
