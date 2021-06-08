"""
File used for testing. 

TODO: Testing plan and motivation
- Test last 10 commits
"""
import os
from git import Repo, Git
import ast
import pickle
import networkx as nx

# Get the tree of the first commit for testing
current_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(current_dir, "module_data")
with open(os.path.join(data_path, "snorkel"), "rb") as file:
    ast_dict = pickle.load(file)
first_graph = ast_dict[list(ast_dict.keys())[1]]

# for n in first_graph.nodes:
#     print(f"The children of {n}: {list(first_graph.successors(n))}")


### Node Testing ###
# root = parsing.Node(parsing.repo_name, None, None)

# f1 = ["setup.py"]
# f1_path = os.sep.join([parsing.repo_path] + f1)
# with open(f1_path) as fin:
#     text = fin.read()
#     ast1 = ast.parse(text)
# t1 = parsing.create_branch(root, f1, ast1)

# f2 = ["docs", "conf.py"]
# f2_path = os.sep.join([parsing.repo_path] + f2)
# with open(f2_path) as fin:
#     text = fin.read()
#     ast2 = ast.parse(text)
# t2 = parsing.create_branch(root, f2, ast2)

# f3 = ["scripts", "check_requirements.py"]
# f3_path = os.sep.join([parsing.repo_path] + f1)
# with open(f3_path) as fin:
#     text = fin.read()
#     ast3 = ast.parse(text)
# t3 = parsing.create_branch(root, f3, ast3)

# f4 = ["scripts", "sync_api_docs.py"]
# f4_path = os.sep.join([parsing.repo_path] + f1)
# with open(f4_path) as fin:
#     text = fin.read()
#     ast4 = ast.parse(text)
# t4 = parsing.create_branch(root, f4, ast4)

# print(t4.to_string())
