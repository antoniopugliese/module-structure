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

def calculate_svd(matrix):
	"""
	Calculates the singular value decomposition from a matrix.

	:param matrix: a sparse matrix representing a NetworkX graph
	:type matrix: scipy.sparse

	:return: a unitary matrix
	:rtype: ndarray
	"""
	return sp.linalg.svd(matrix)

def calculate_eig(graph, spectrum = "adjacency"):
	"""
	Calculates the eigenvalues from the matrix.

	:param graph: a NetworkX graph
	:type graph: NetworkX graphh

	:return: the eigenvalues of the matrix
	:rtype: Numpy array
	"""
	if spectrum == "adjacency":
		return nx.adjacency_spectrum(graph)
	elif spectrum == "laplacian":
		return nx.laplacian_spectrum(graph)
	elif spectrum == "bethe":
		return nx.bethe_hessian_spectrum(graph)
	elif spectrum == "normalized":
		return nx.normalized_laplacian_spectrum(graph)
	elif spectrum == "modularity":
		return nx.modularity_spectrum(graph)