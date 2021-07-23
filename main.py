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

    :param name: the name of the object being stored
    :type name: str

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

    :param name: the name of the object being stored
    :type name: str

    :param key: represents the key for the database
    :type key: str 

    :return: the value associated with the key
    :rtype: Multiple types
    """
    try:
        return pickle.loads(rs.hget(name, key))
    except TypeError:
        return None


def get_repo(rs, repo_name, start):
    """
    Gets the repo path from file directory. 

    :param rs: the Redis database
    :type rs: Redis

    :param repo_name: the name of the repo
    :type repo_name: str

    :param home: the start directory
    :type home: str

    :return: the path of the repo
    :rtype: str
    """
    repo_path = get_from_database(rs, repo_name, "repo_path")

    # If the repo_path is not in the database, scan the directory to find it
    if repo_path is not None:
        print("Found a path")
    else:
        print("Scanning start directory...", end="", flush=True)
        repo_path = parsing.find_dir(start, repo_name)
        print(repo_path)
        add_to_database(rs, repo_name, "repo_path", repo_path)
        print("Done")

    return repo_path


def find_repo(rs, repo_name, repo_link, dir):
    repo_path = get_from_database(rs, repo_name, "repo_path")

    if repo_path is not None:
        print("Found path.")
    else:
        print("Cloning from git...", end="", flush=True)
        new_dir = os.path.join(dir, "frontend", "module_data")
        os.chdir(new_dir)
        clone = f"git clone {repo_link}"
        os.system(clone)
        repo_path = parsing.find_dir(new_dir, repo_name)
        add_to_database(rs, repo_name, "repo_path", repo_path)
        os.chdir(dir)
        print("Done")

    return repo_path


def main_db():
    # Initialize the redis database (database 0)
    rs = redis.Redis(db=0)

    # Locations in file directory w.r.t local device
    home = os.path.expanduser("~")
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Opening the config file
    with open(os.path.join(current_dir, "config.json"), "r") as f:
        config = json.load(f)

    repo_name = config["repo_name"]
    repo_link = config["repo_link"]

    print("Finding path to target repo...", end="", flush=True)

    # repo_path = get_repo(rs, repo_name, home)
    repo_path = find_repo(rs, repo_name, repo_link, current_dir)

    try:
        os.chdir(repo_path)
    except OSError:
        print("Error changing directory")

    # Create Repo object and extract list of commits
    repo = Repo(repo_path)
    assert not repo.bare
    g = Git(repo_path)
    g.checkout(config["branch"])
    # Limited to 10 for testing
    commits = list(repo.iter_commits(
        config["branch"], max_count=config["max_count"]))

    print("Checking if file is in database...", end="", flush=True)

    ast_dict = get_from_database(rs, repo_name, "ast_dict")

    # If the ast_dict is not in the database, create the ast_dict
    if ast_dict is not None:
        print("ASTs have been found.")
        ast_dict = parsing.update_ast_dict(
            ast_dict, commits, repo_path, repo_name, g)
        add_to_database(rs, repo_name, "ast_dict", ast_dict)
    else:
        print("ASTs are not found...", end="", flush=True)
        ast_dict = parsing.create_ast_dict(commits, repo_path, repo_name, g)
        add_to_database(rs, repo_name, "ast_dict", ast_dict)
        print("ASTs have been created")

    print("Checking if relationships have been formed...", end="", flush=True)

    commit_dict = get_from_database(rs, repo_name, "commit_dict")

    # If the commit_dict is not in the database, create thhe commit_dict
    if commit_dict is not None:
        print("Found the commit history.")
    else:
        print("Commit history not found.")
        commit_dict = dict(map(lambda key:
                               (key, rel.create_all_relationships(ast_dict[key])), ast_dict))
        print("Storing relationships...", end="", flush=True)
        add_to_database(rs, repo_name, "commit_dict", commit_dict)
        print("Done!")

    latest_commit = "39dc1c46adcb3b8500b4e232fbe0efc41e65f0e1"
    latest_graph = rel.create_all_relationships(ast_dict[latest_commit])
    # print("List of nodes: ", list(latest_graph.nodes))
    # print("List of edges: ", list(latest_graph.edges))

    graph_data = rel.graph_to_json(latest_graph)

    latest_commit += ".json"

    data_path = os.path.join(current_dir, "frontend", "module_data")
    if not os.path.isdir(data_path):
        os.mkdir(data_path)
    with open(os.path.join(data_path, latest_commit), "w") as f:
        json.dump(graph_data, f, indent=4)

    print("Displaying graph.\n")

    # save updated data (if any)
    rs.execute_command('BGSAVE SCHEDULE')
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
    data_path = os.path.join(current_dir, "frontend", "module_data")

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


if __name__ == "__main__":
    # main()
    main_db()
