"""
File used for testing. 

TODO: Testing plan and motivation
"""
import os
from git import Repo, Git
import ast
import parsing

### Node Testing ###
root = parsing.Node(parsing.repo_name, None, None)

f1 = ["setup.py"]
f1_path = os.sep.join([parsing.repo_path] + f1)
with open(f1_path) as fin:
    text = fin.read()
    ast1 = ast.parse(text)
t1 = parsing.create_branch(root, f1, ast1)

f2 = ["docs", "conf.py"]
f2_path = os.sep.join([parsing.repo_path] + f2)
with open(f2_path) as fin:
    text = fin.read()
    ast2 = ast.parse(text)
t2 = parsing.create_branch(root, f2, ast2)

f3 = ["scripts", "check_requirements.py"]
f3_path = os.sep.join([parsing.repo_path] + f1)
with open(f3_path) as fin:
    text = fin.read()
    ast3 = ast.parse(text)
t3 = parsing.create_branch(root, f3, ast3)

f4 = ["scripts", "sync_api_docs.py"]
f4_path = os.sep.join([parsing.repo_path] + f1)
with open(f4_path) as fin:
    text = fin.read()
    ast4 = ast.parse(text)
t4 = parsing.create_branch(root, f4, ast4)

print(t4.to_string())