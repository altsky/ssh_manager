# SSH Manager

[Русская версия](./README.ru.md)

## Description
SSH Manager is a CLI tool for connecting to SSH hosts and conveniently editing them interactively, with the ability to group hosts by projects. It is suitable for developers, DevOps engineers, and anyone who works with multiple SSH servers.

### Why SSH Manager?
- **Convenient SSH manager**: More convenient than constantly editing `~/.ssh/config`. SSH hosts and their parameters are stored in a `json` file, allowing flexible configuration of each host and grouping hosts by projects.
- **Fast host selection**: Uses fzf for instant search and selection of a host to connect to.
- **Interactive editing**: Add, edit, and delete hosts and projects through a simple menu.

---

## Requirements
- Linux, macOS
- Python 3
- jq
- fzf

---

## Installation (macOS example)
1. Create the directory `~/.ssh/ssh_manager/` and copy the files `ssh_manager.py` and `ssh_connect` into it:
   ```bash
   mkdir -p ~/.ssh/ssh_manager
   cp ssh_manager.py ssh_connect ~/.ssh/ssh_manager/
   ```
2. Make the `ssh_connect` script executable:
   ```bash
   chmod +x ~/.ssh/ssh_manager/ssh_connect
   ```
3. (Optional) Add the script directory to your `PATH` to run the program from anywhere, or add an alias for launching `ssh_connect` with a short command. Open your `~/.bashrc`, `~/.zshrc`, or other shell config file and add:
    ```bash
    export PATH="$HOME/.ssh/ssh_manager:$PATH"
    ```
    or
    ```bash
    alias sshm="$HOME/.ssh/ssh_manager/ssh_connect"
    ```
    *The following instructions assume you have completed this step*

4. Make sure the dependencies are installed:
   ```bash
   brew install jq fzf
   ```

---

## Usage

### Connecting to a host
1. Enter
```bash
sshm
```
2. Select the desired host from the list and press Enter. Or start typing the host name to filter the list to only those hosts containing your input.

### Managing hosts and projects (interactive menu)
1. Enter
```bash
sshm --hosts
# or
sshm -h
```
2. Select a menu item and follow the on-screen instructions.

---

## Configuration example
See [hosts.json](./hosts.json) — an example file with several projects and hosts.
