import os
import parsing
import json
import pickle
import relationship as rel
import visual
import metrics
import matrix as mat
from git import Repo, Git


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

    print("Creating relationships...", end="", flush=True)
    commit_list = list(ast_dict.keys())
    graph_dict = {}

    for commit in commit_list:
        new_graph = rel.definition_nodes(ast_dict[commit])
        rel.import_relationship(new_graph)
        rel.function_call_relationship(new_graph)
        rel.inheritance_relationship(new_graph)
        matrix = mat.graph_to_matrix(new_graph)
        graph_dict.update({commit: (new_graph, matrix)})

    print("Done.")

    first = commit_list[0]
    tup = graph_dict.get(first)
    visual.display(tup[0])

    # commit_dict = dict(map(lambda key:
    #                        (key, rel.create_all_relationships(ast_dict[key])), ast_dict))

    # first = commit_list[0]
    # visual.display(commit_dict.get(first))

    # commit with sha1='b6823ffbe00ee1730101582390e50eeba0361f27' was the latest
    # commit to add a file: snorkel/types/hashing.py
    # remember to add relationships to graphs in ast_dict, and change max commits
    # to 25 in config.json
    # metrics.unique_subgraphs(commit_dict, "file directory")


if __name__ == "__main__":
    main()
