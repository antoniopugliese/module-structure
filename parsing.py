"""
Initial docstring for the parsing module
"""


import os
from git import Repo, Git
import ast

repo_name = "snorkel"

# git_path = os.getcwd().split(os.sep)[:-1]
# git_path.append(repo_name)
# repo_path = os.sep.join(git_path)
# ### needs work
#
# repo = Repo(repo_path)
# assert not repo.bare
# g = Git(repo_path)
# g.checkout('master')
# commits = list(repo.iter_commits('master'))
#
# for commit in commits:
#     sha1 = commit.hexsha
#     g.checkout(sha1)
#     files = g.ls_files()
#
#     for file in files:
#         if not file.endswith('.py'):
#             continue
#         with open(filename) as fin:
#             text = fin.read()
#             tree = ast.parse(text)
