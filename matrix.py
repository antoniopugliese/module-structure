"""
This module will take in a NetworkX graph and construct an adjacency matrix from
this graph. 
"""
import networkx as nx
import scipy as sp
import numpy as np

def graph_to_matrix(graph, order = None, weight = None):
	"""
	Converts a NetworkX graph into an adjacency matrix. 

	:param graph: a NetworkX graph
	:type graph: NetworkX graphh

	:param order: a list or ordered nodes in the NetworkX graph
	:type order: Node list

	:param weight: represents which weight will be represented in the matrix
	:type weight: int

	:return: a sparse matrix representation of the graph
	:rtype: scipy.sparse
	"""
	return nx.adjacency_matrix(graph, order, weight)

def calculate_svd(matrix):
	"""
	Calculates the singular value decomposition from a matrix.

	:param matrix: a sparse matrix representing a NetworkX graph
	:type matrix: scipy.sparse

	:return: a unitary matrix
	:rtype: ndarray
	"""
	return sp.linalg.svd(matrix)