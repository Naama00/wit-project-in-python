# Wit - Version Control System 🚀

A modular VCS built with Python.

### 🛠 Installation

1. Update environment tools:
pip install click setuptools
2. Install requirements:
pip install -r requirements.txt
3. Setup the 'wit' command:
pip install -e .

---

### 🚀 Available Commands

| Command | Action |
| :--- | :--- |
| **wit init** | Initialize a new repository |
| **wit add <path>** | Stage a file or folder |
| **wit commit -m "msg"** | Create a new snapshot |
| **wit status** | Show working tree status |
| **wit log** | Show commit history |
| **wit checkout <id>** | Switch to a specific version |

---

### 📂 Structure
- **wit_cli.py**: CLI Entry point
- **wit_core.py**: Logic & Implementation
- **utils.py**: Helper functions
- **setup.py**: Installation config