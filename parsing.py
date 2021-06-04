"""
This module constructs an object representing the file structure and the abstract
syntax tree (AST) for every Python code file in a given git repo.

This module creates a dictionary object mapping the SHA1 hash of a commit of a git
repo to a custom object that maintains information about the directory of the git
repo, and the AST of every Python code file. A user can modify the ``config.json``
file to alter what commits are analyzed.

Requires Python 3.8.3 or above. 
"""
import os
from git import Repo, Git
import ast
import json
import pickle


class Node():
    """
    This Node class is used to build a tree that represents a software module.
    Each Node represents either a folder or Python file. 

    If the Node is a leaf of a tree, an instance contains the name of a Python 
    file, its AST, and a reference to its parent directory.

    Otherwise, an instance contains the name of a directory, a reference to its
    parent directory (if any), and a list of children Nodes.
    """

    def __init__(self, n, ast, p):
        """
        Initializes the Node object. The Node will contain the name `n`,
        a given AST `ast` (which could be ``None``), and a reference to the parent
        Node `p`. The Node object intially has no children.

        :param n: name of the instance (file or directory) 
        :type n: str

        :param ast: the abstract syntax tree of n if a file, None otherwise
        :type ast: ast.Module 

        :param p: the parent of the Node object, None if doesn't exist
        :type p: Node

        :param children: the children of the Node object, initially empty
        :type children: Node list

        :return: A Node object containing, n, ast, and p.
        :rtype: Node

        For example, to create a Node to represent a root folder named "src":
        >>> Node("src", None, None)
        """
        self.name = n
        self.tree = ast
        self.parent = p
        self.children = []

    def add_child(self, child):
        """
        Adds a child to the Node object. 

        :param child: Node object to add to tree. 
        :type child: Node

        :return: Node object with child added to its list of children
        :rtype: Node 

        >>> example = Node('example', None, None)
        >>> example.add_child(Node('child_1', None, 'example'))
        >>> example.add_child(Node('child_2', None, 'example'))
        >>> example.children
        [Node('child_1',None,'example'), Node('child_2', None, 'example')]
        """
        self.children.append(child)

    def to_string(self, level=0):
        """
        String representation of a Node and all its children. Mainly used for 
        debugging purposes. 

        :param level: the current depth of the Node, defaults to 0.
        :type level: int

        :return: A string representing the Node and all its children
        :rtype: str

        >>> example = Node('example', None, None)
        >>> example.to_string()
        'example'

        >>> example.add_child(Node('child', None, example))
        >>> example.to_string()
        'example'
            'child'
        """
        base = self.name + "\n"
        level += 1
        for child in self.children:
            base += " "*4*level + child.to_string(level)
        return base


def find_dir(start, target):
    """
    Finds the path of a target directory given a start directory.
    Assumes a top-down approach will be taken.

    :param start: the path of the directory where the search starts
    :type start: str

    :param target: the name of the target directory
    :type target: str

    :return: path of the target directory
    :rtype: str

    >>> home = os.path.expanduser("~")
    >>> repo_name = 'snorkel'
    >>> find_dir(repo_name, home)
    'C:\\Users\\Antonio\\Documents\\GitHub\\snorkel'
    """
    for path, dirs, files in os.walk(start):
        # If the target directory is within current list of directories
        if target in dirs:
            return os.path.join(path, target)


def create_branch(tree, filepath, ast):
    """
    Adds a leaf to `tree` to represent the file structure of the Python file
    given by `filepath`. The leaf contains the AST of the Python file.

    :param tree: the existing tree the branch will be added to
    :type tree: Node

    :param filepath: the sequence of directories to the target Python file
    :type filepath: str list

    :param ast: the AST object of the target Python file
    :type ast: ast

    :return: leaf to the `tree` that contains the AST of the Python file
    :rtype: Node
    """
    # the name of "folder" or Python file
    name = filepath[0]

    # if at the Python file
    if (len(filepath) == 1):
        # add AST to the leaf
        tree.add_child(Node(name, ast, tree))
        return tree
    else:
        filepath.pop(0)
        branch_exists = False
        # if "folder" already is in the tree, add the branch starting from that
        # folder
        for child in tree.children:
            if (child.name == name):
                create_branch(child, filepath, ast)
                branch_exists = True
                break
        # create the "folder", and then add the branch
        if (not branch_exists):
            tree.add_child(Node(name, None, tree))
            create_branch(tree.children[-1], filepath, ast)
        return tree


def create_ast_value(files, repo_path):
    """
    Creates a new `tree` of Nodes based on a list of files. 

    :param files: list of files
    :type files: str list

    :param repo_path: the path to the directory that contains the target repo
    :type repo_path: str

    :return: a `tree` of Nodes based on the files in repo_path
    :rtype: Node
    """
    # create root
    root = Node(repo_name, None, None)

    for file in files:
        if file.endswith('.py'):
            # print(file)
            file_dir = file.split('/')
            file_path = os.sep.join([repo_path] + file_dir)
            with open(file_path) as fin:
                text = fin.read()
                try:
                    tree = ast.parse(text)
                    create_branch(root, file_dir, tree)
                except SyntaxError:
                    pass
                    # if the code that ast parses has a syntax error, it causes
                    # the function call to result in a syntax error.

    return root


def create_ast_dict(commits):
    """
    Creates a dictionary mapping the SHA1 of each version in `commits` to a Node
    object that contains the abstract syntax trees of all the Python code in that
    version.

    :param commits: the list of commits in a repo
    :type commits: Git.Commit list

    :return: a dictionary mapping the SHA1 of each commit to a Node object. 
    :rtype: dictionary {str : Node}
    """

    # Side effect for testing
    print("Creating ast dictionary...", end="", flush=True)

    ast_dict = {}

    for commit in commits:
        sha1 = commit.hexsha
        g.checkout(sha1)
        # get list of file paths from repo dir
        files = g.ls_files().split('\n')
        assert files != None

        # create tree
        root = create_ast_value(files, repo_path)

        ast_dict.update({sha1: root})

    # Side effect for testing
    print("Done.")
    return ast_dict


def update_ast_dict(dict, commits, repo_path):
    """
    Updates the dictionary to add any new commits in a repo. 

    :param dict: dictionary that maps SHA1 to a Node object
    :type dict: dictionary {str : Node} 

    :param commits: the list of commits in a repo
    :type commits: Git.Commit list

    :return: An updated dictionary with any new commits. 
    :rtype: dictionary {str : Node} 
    """

    # loop through commits
    # Improve this

    # for i in range(0, len(commits)):
    #     commit = commits[i]
    #     if (i % 100 == 0):
    #         print(f"{i} commits done.")
    print("Updating the dictionary...", end="", flush=True)
    for commit in commits:
        sha1 = commit.hexsha
        if dict.get(sha1) == None:
            g.checkout(sha1)
            files = g.ls_files().split('\n')
            assert files != None

            root = create_ast_value(files, repo_path)

            dict.update({sha1: root})

    print("Done.")
    return dict


if __name__ == "__main__":
    home = os.path.expanduser("~")

    ### potentially need to find path to config.json as well ###
    with open("config.json", "r") as f:
        config = json.load(f)

    repo_name = config["repo_name"]

    # Find absolute current directory path
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Path to file containing pickled data
    data_path = os.path.join(current_dir, "module_data")

    # Recursively determine where target repo is based on home directory
    print("Finding path to target repo...", end="", flush=True)

    try:
        with open(os.path.join(data_path, repo_name + "_path"), "rb") as file:
            repo_path = pickle.load(file)
        print("Found path.")
    except (FileNotFoundError):
        print("Scanning start directory...", end="", flush=True)
        repo_path = find_dir(home, repo_name)
        print("Done.")
        if not os.path.isdir(data_path):
            os.mkdir(data_path)
        with open(os.path.join(data_path, repo_name + "_path"), "wb") as file:
            pickle.dump(repo_path, file, protocol=pickle.HIGHEST_PROTOCOL)

    try:
        os.chdir(repo_path)
    except OSError:
        print("Error changing directory")

    # create Repo object and extract list of commits
    repo = Repo(repo_path)
    assert not repo.bare
    g = Git(repo_path)
    g.checkout(config["branch"])
    # limited to 10 for testing
    commits = list(repo.iter_commits('master', max_count=config["max_count"]))

    try:
        print("Checking if file has been pickled...", end="", flush=True)
        if os.path.exists(os.path.join(data_path, repo_name)):
            print("Found a file.")
        with open(os.path.join(data_path, repo_name), "rb") as file:
            ast_dict = pickle.load(file)
        file.close()
        ast_dict = update_ast_dict(ast_dict, commits, repo_path)
    except (FileNotFoundError):
        # Create dictionary
        print("Not Found.")
        ast_dict = create_ast_dict(commits)
        file.close()

    # store the pickled dictionary
    with open(os.path.join(data_path, repo_name), "wb") as file:
        pickle.dump(ast_dict, file, protocol=pickle.HIGHEST_PROTOCOL)

    # print file structure of the latest commit
    # print("Printing the AST")
    # first = list(ast_dict.keys())[1]
    # print(ast_dict[first].to_string())
