# ALTER IGO: TALK TO YOUR DATA

---

## Overview

Alter Igo is an application built using OpenAI's Codex model that can be used to generate and execute code from commands provided using natural language. Currently, the application supports commands written in the following languages:
- English

The model currently generates code in the following languages:
- Python

## Architecture

The backend is built on Python and Flask. Dependencies can be found in the `requirements.txt` file.

The frontend is built using HTML, CSS, and JavaScript. JavaScript is also used to communicate with the backend for processing user inputs and actions.

## Usage

1. Clone the repository into a local directory
2. Activate a virtual environment and install all dependencies
    - `python -m venv .venv` (to create a virtual environment in the `.venv` directory)
    - `source .venv/bin/activate` (to activate the virtual environment - Linux/Mac)
    - `.venv/Scripts/activate` (to activate the virtual environment - Windows)
    - `pip install -r requirements.txt` (to install all dependencies)
3. Run the application from the root project folder using `python wsgi.py`
4. By default, the application will automatically choose an available port to run on using the local host IP address. The command line output will indicate the address and port number where the application is running

## Features

- Single and multi-line commands are supported (Enter to line-break, Ctrl+Enter to submit)
- Rendering of dataframes as tables / plots as images
- Editing commands and code blocks
- Deletion of entries (command + corresponding code block) from the history
- Thumbs up/down to rate the quality of the generated code and output
    - This will help us to fine-tune the model to generate better code in the future

## Help

By default, the traceback of any errors will be displayed. This can help with troubleshooting code that didn't run properly (e.g. missing an import). Users can edit the code to insert or fix code, then re-submit it.

I've made an effort to comment the code as much as possible, which may help with understanding what's going on behind the scenes. For further questions, please raise an issue or contact me at [mailto:felix.peng@zs.com](mailto:felix.peng@zs.com).
