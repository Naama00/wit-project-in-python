# Wit Version Control System

A lightweight, Python-based Version Control System (VCS) inspired by Git. Built for educational purposes to demonstrate how snapshots and staging work.



## 🚀 Key Features
* **Init:** Initialize a new `.wit` repository in your current directory.
* **Add:** Stage files or directories (supports `.witignore`).
* **Commit:** Save permanent snapshots with unique IDs and custom messages.
* **Status:** Compare differences between your working directory, staging, and the last commit.
* **Checkout:** Instantly restore the project to any previous state using a Commit ID.
* **Log:** View the full history of your project's evolution.

## 🛠 Installation & Setup

1. **Prerequisites:** Ensure you have **Python 3.x** installed.
2. **Dependencies:** This project uses the `click` library for the CLI interface.
   ```bash
   pip install click