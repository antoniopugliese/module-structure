# Module-Structure

## Overview

This research repo is a tool to analyze Git repositories of Python code for internal dependency relationships. Give a link to a Git repository (or a path to an already downloaded repositiory) and the tool will create a graph representation of import, function call, class inheritance, and other relationships between Python files.

Relationships can be as broad as directories in a repo, to the granularity of variable usage within Python files.

Run the frontend to interactively explore various relationship graphs and discover insights into your repository. Use several pre-made presets showing useful data, or customize a view with any combination of node or relationship types.  

Use the backend modules to create a Python `networkx` graph representation of a Git repo for your own analysis.

## Installation 
Requires Python ### or later. Clone this repository to use its tools and run the interface. 
The local web server runs **Node.js** and uses **npm** to manage dependencies.

<details><summary><b>Install Python Dependencies</b></summary>
<p>

Navigate to the directory of the cloned repository and run:
```python
pip install -r requirements.txt
```

</p>
</details>

<details><summary><b>Install Node.js</b></summary>
<p>

If not already done, [download Node.js](https://nodejs.org/en/download/).

</p>
</details>

<details><summary><b>Install dependencies</b></summary>
<p>

To install the Node.js dependencies:
```bash
npm install
```

</p>
</details>


## Run Local Server with Web App
Navigate to the root of the cloned repository and run:
```bash
node frontend/proxy_server.js
```
Use any browser to navigate to localhost for the port returned.

## Run Python Dash Interface
The Dash app uses a Redis database. 

<details><summary><b>Working with Redis</b></summary>
<p>

While Redis runs best on Linux, there is a Windows version. See their [quickstart](https://redis.io/topics/quickstart) for installation.

See the [guide](./redis-setup.md) to configuring and starting a Redis database.

</p>
</details>

After starting a Redis database, run:
```
python main.py
```
The web app will automatically open on the last used web browser.





