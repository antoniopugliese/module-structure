import os
import parsing
import json
import pickle
import relationship as rel
import visual
from git import Repo, Git
import redis


def add_to_database(rs: redis.Redis, name, key, value):
    """
    Adds a key and value to a database.

    :param rs: a redis database
    :type rs: redis.Redis

    :param key: represents the key to be added for the database
    :type key: str

    :param value: represents the value to be added for the database
    :type value: byte
    """
    rs.hset(name, key, pickle.dumps(value))


def get_from_database(rs: redis.Redis, name, key):
    """
    Gets the value corresponding to a key.

    :param rs: a redis database
    :type rs: redis.Redis

    :param key: represents the key for the database
    :type key: str 

    :return: the value associated with the key
    :rtype: Multiple types
    """
    try:
        return pickle.loads(rs.hget(name, key))
    except TypeError:
        return None


def main_db():
    rs = redis.Redis(db=0)
    home = os.path.expanduser("~")
    current_dir = os.path.dirname(os.path.abspath(__file__))

    with open(os.path.join(current_dir, "config.json"), "r") as f:
        config = json.load(f)

    repo_name = config["repo_name"]

    print("Finding path to target repo...", end="", flush=True)

    repo_path = get_from_database(rs, repo_name, "repo_path")

    if repo_path is not None:
        print("Found path.")
    else:
        print("Scanning start directory...", end="", flush=True)
        repo_path = parsing.find_dir(home, repo_name)
        add_to_database(rs, repo_name, "repo_path", repo_path)

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
    commits = list(repo.iter_commits(
        config["branch"], max_count=config["max_count"]))

    print("Checking if file is in database...", end="", flush=True)

    ast_dict = get_from_database(rs, repo_name, "ast_dict")

    if ast_dict is not None:
        print("Found.")
        ast_dict = parsing.update_ast_dict(
            ast_dict, commits, repo_path, repo_name, g)
    else:
        print("Not Found.")
        ast_dict = parsing.create_ast_dict(commits, repo_path, repo_name, g)
        add_to_database(rs, repo_name, "ast_dict", ast_dict)

    print("Checking if relationships have been formed...", end="", flush=True)

    commit_dict = get_from_database(rs, repo_name, "commit_dict")

    if commit_dict is not None:
        print("Found a file.")
    else:
        print("Not Found.")
        commit_dict = dict(map(lambda key:
                               (key, rel.create_all_relationships(ast_dict[key])), ast_dict))
        print("Storing relationships...", end="", flush=True)
        add_to_database(rs, repo_name, "commit_dict", commit_dict)
        print("Done.")

    print("Done.\n")

    visual.display(repo_name, rs, commits, commit_dict)


def main():
    home = os.path.expanduser("~")
    # Find absolute current directory path
    current_dir = os.path.dirname(os.path.abspath(__file__))

    ### potentially need to find path to config.json as well ###
    with open(os.path.join(current_dir, "config.json"), "r") as f:
        config = json.load(f)

    repo_name = config["repo_name"]

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
        repo_path = parsing.find_dir(home, repo_name)
        print("Done")
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
    commits = list(repo.iter_commits(
        config["branch"], max_count=config["max_count"]))

    try:
        print("Checking if file has been pickled...", end="", flush=True)
        if os.path.exists(os.path.join(data_path, repo_name)):
            print("Found a file.")
        with open(os.path.join(data_path, repo_name), "rb") as file:
            ast_dict = pickle.load(file)
        file.close()
        ast_dict = parsing.update_ast_dict(
            ast_dict, commits, repo_path, repo_name, g)
    except (FileNotFoundError):
        # Create dictionary
        print("Not Found.")
        ast_dict = parsing.create_ast_dict(commits, repo_path, repo_name, g)
        file.close()

    # store the pickled dictionary
    print("Storing dictionary...", end="", flush=True)
    with open(os.path.join(data_path, repo_name), "wb") as file:
        pickle.dump(ast_dict, file, protocol=pickle.HIGHEST_PROTOCOL)
    print("Done.")

    #commit_list = list(ast_dict.keys())
    # graph_dict = {}

    # for commit in commit_list:
    #     new_graph = rel.create_all_relationships(ast_dict[commit])
    #     matrix = mat.graph_to_matrix(new_graph)
    #     eigenvalues = mat.calculate_eig(new_graph)
    #     graph_dict.update({commit: (new_graph, matrix, eigenvalues)})

    # print("Done.")

    # first = commit_list[0]
    # tup = graph_dict.get(first)
    # visual.display(tup[0])

    # commit_dict = dict(map(lambda key:
    #                        (key, rel.create_all_relationships(ast_dict[key])), ast_dict))

    # first = commit_list[0]
    # tup = graph_dict.get(first)
    # visual.display(tup[0])

    # just for testing since it takes a while for 25 commits
    try:
        print("Checking if relationships have been formed...", end="", flush=True)
        if os.path.exists(os.path.join(data_path, repo_name + "_analysis")):
            print("Found a file.")
        with open(os.path.join(data_path, repo_name + "_analysis"), "rb") as file:
            commit_dict = pickle.load(file)
        # need to add updating feature
        file.close()
    except (FileNotFoundError):
        # Create dictionary
        print("Not Found.")
        commit_dict = dict(map(lambda key:
                           (key, rel.create_all_relationships(ast_dict[key])), ast_dict))
        print("Storing relationships...", end="", flush=True)
        with open(os.path.join(data_path, repo_name + "_analysis"), "wb") as file:
            pickle.dump(commit_dict, file, protocol=pickle.HIGHEST_PROTOCOL)
        print("Done.")
    file.close()
    print("Done.\n")

    visual.display(commits, commit_dict)


if __name__ == "__main__":
    # main()
    main_db()
