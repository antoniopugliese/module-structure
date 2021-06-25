"""
This module will take in a NetworkX graph and construct an adjacency matrix from
this graph. 
"""
import networkx as nx
import scipy as sp
import numpy as np

def graph_to_matrix(graph, order = None, weight = None, matrix = "adjacency"):
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
	if matrix == "adjacency":
		return nx.adjacency_matrix(graph, order, weight)
	elif matrix == "laplacian":
		return nx.laplacian_matrix(graph, order, weight)
	elif matrix == "normalized":
		return nx.normalized_laplacian_matrix(graph, order, weight)
	elif matrix == "directed":
		return nx.directed_laplacian_matrix(graph, order, weight)
	elif matrix == "combinatorial":
		return nx.directed_combinatorial_laplacian_matrix(graph, order, weight)	

def analyze_matrix(matrix, type = "eig"):
	"""
	Calculates the singular values or eigenvalues from a matrix.

	:param matrix: a sparse matrix representing a NetworkX graph
	:type matrix: scipy.sparse

	:param type: either singular values or eigenvalues
	:type type: str

	:return: a unitary matrix
	:rtype: ndarray
	"""
	if type == "eig":
		return sp.linalg.svd(matrix)
	elif type == "svd":
		return sp.linalg.eig(matrix)