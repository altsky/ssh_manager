import json
import os
import subprocess
import shutil

CONFIG_FILE = os.path.expanduser("~/.ssh/ssh_manager/hosts.json")


def load_config():
    if not os.path.exists(CONFIG_FILE):
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        return {"projects": []}
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading config file: {e}")
        print("Using empty configuration.")
        return {"projects": []}


def save_config(config):
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    except IOError as e:
        print(f"Error saving config file: {e}")
        return False
    return True


def run_fzf(items, prompt="Select an option:"):
    if not items:
        print("No items to select from.")
        return ""

    import tempfile

    try:
        # Create temporary file with items
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp_file:
            tmp_file.write('\n'.join(items))
            tmp_filename = tmp_file.name

        # Run fzf with direct terminal access (no capture_output to allow interaction)
        fzf_command = f"fzf --prompt '{prompt}' < {tmp_filename} 2>/dev/null"
        process = subprocess.Popen(
            fzf_command, shell=True, stdout=subprocess.PIPE, text=True)
        stdout, _ = process.communicate()

        # Clean up temp file
        os.unlink(tmp_filename)

        if process.returncode == 0:
            return stdout.strip()
        else:
            return ""

    except FileNotFoundError:
        print("Error: fzf not found. Please install fzf.")
        return ""
    except Exception as e:
        print(f"Error running fzf: {e}")
        return ""


def backup_config():
    if os.path.exists(CONFIG_FILE):
        shutil.copy(CONFIG_FILE, CONFIG_FILE + ".bak")


def select_project(config, prompt="Select a project:"):
    project_names = [p['name'] for p in config['projects']]
    if not project_names:
        print("No projects found. Please add a project first.")
        return None
    selected = run_fzf(project_names, prompt=prompt)
    if not selected:
        print("No project selected.")
        return None
    return next((p for p in config['projects'] if p['name'] == selected), None)


def select_host(config, prompt="Select a host:"):
    all_hosts = []
    for p in config['projects']:
        for h in p['hosts']:
            all_hosts.append(
                f"{p['name']} | {h['name']} | {h.get('addr', '')}")
    if not all_hosts:
        print("No hosts found.")
        return None, None, None
    selected = run_fzf(all_hosts, prompt=prompt)
    if not selected:
        print("No host selected.")
        return None, None, None
    project_name, host_name, _ = selected.split(' | ', 2)
    project = next(
        (p for p in config['projects'] if p['name'] == project_name), None)
    host = next((h for h in project['hosts'] if h['name']
                == host_name), None) if project else None
    return project, host, selected


def add_host(config):
    print("\n--- Add New Host ---")
    project = select_project(config, prompt="Select a project to add host to:")
    if not project:
        return
    host_name = input("Enter host name (e.g., web-server-01): ").strip()
    if not host_name:
        print("Host name cannot be empty.")
        return
    if any(h['name'] == host_name for h in project['hosts']):
        print(
            f"Host with name '{host_name}' already exists in project '{project['name']}'.")
        return
    host_addr = input("Enter host address (IP or FQDN): ").strip()
    if not host_addr:
        print("Host address cannot be empty.")
        return
    host_port = input(
        f"Enter port for {host_name} (default: {project.get('port', '22')}): ").strip()
    host_user = input(
        f"Enter user for {host_name} (default: {project.get('user', '')}): ").strip()
    host_key = input(
        f"Enter path to SSH key for {host_name} (default: {project.get('key', '')}): ").strip()
    new_host = {"name": host_name, "addr": host_addr}
    if host_user:
        new_host['user'] = host_user
    if host_key:
        new_host['key'] = host_key
    if host_port:
        new_host['port'] = host_port
    backup_config()
    project['hosts'].append(new_host)
    if save_config(config):
        print(f"Host {host_name} added to project {project['name']}.")
    else:
        print("Error: Failed to save configuration.")


def edit_host(config):
    print("\n--- Edit Host ---")
    project, host, selected = select_host(
        config, prompt="Select a host to edit:")
    if not host:
        return
    print(f"Editing host: {host['name']} (Project: {project['name']})")

    # Get current effective values (host value or fallback to project value)
    current_user = host.get('user', project.get('user', ''))
    current_key = host.get('key', project.get('key', ''))
    current_port = host.get('port', project.get('port', '22'))

    new_name = input(f"New host name (current: {host['name']}): ").strip()
    if new_name and new_name != host['name']:
        if any(h['name'] == new_name for h in project['hosts']):
            print(
                f"Host with name '{new_name}' already exists in project '{project['name']}'.")
            return
        host['name'] = new_name

    new_addr = input(
        f"New address (current: {host.get('addr', '')}): ").strip()
    if new_addr:
        host['addr'] = new_addr

    new_port = input(f"New port (current: {current_port}): ").strip()
    if new_port:
        if new_port != project.get('port', '22'):
            # Only save port if it differs from project default
            host['port'] = new_port
        elif 'port' in host:
            # Remove port if it matches project default
            del host['port']
    else:
        # Even with empty input, check if current value duplicates project value
        if 'port' in host and host['port'] == project.get('port', '22'):
            del host['port']

    new_user = input(f"New user (current: {current_user}): ").strip()
    if new_user:
        if new_user != project.get('user', ''):
            # Only save user if it differs from project default
            host['user'] = new_user
        elif 'user' in host:
            # Remove user if it matches project default
            del host['user']
    else:
        # Even with empty input, check if current value duplicates project value
        if 'user' in host and host['user'] == project.get('user', ''):
            del host['user']

    new_key = input(f"New key path (current: {current_key}): ").strip()
    if new_key:
        if new_key != project.get('key', ''):
            # Only save key if it differs from project default
            host['key'] = new_key
        elif 'key' in host:
            # Remove key if it matches project default
            del host['key']
    else:
        # Even with empty input, check if current value duplicates project value
        if 'key' in host and host['key'] == project.get('key', ''):
            del host['key']

    backup_config()
    if save_config(config):
        print(f"Host {host['name']} updated.")
    else:
        print("Error: Failed to save configuration.")


def delete_host(config):
    print("\n--- Delete Host ---")
    project, host, selected = select_host(
        config, prompt="Select a host to delete:")
    if not host:
        return
    confirm = input(
        f"Are you sure you want to delete host '{host['name']}' from project '{project['name']}'? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("Host deletion cancelled.")
        return
    backup_config()
    project['hosts'] = [h for h in project['hosts']
                        if h['name'] != host['name']]
    if save_config(config):
        print(f"Host {host['name']} deleted from project {project['name']}.")
    else:
        print("Error: Failed to save configuration.")


def add_project(config):
    print("\n--- Add New Project ---")
    project_name = input("Enter new project name: ").strip()
    if not project_name:
        print("Project name cannot be empty.")
        return
    if any(p['name'] == project_name for p in config['projects']):
        print(f"Project '{project_name}' already exists.")
        return
    project_port = input(
        "Enter default port for this project (default: 22, optional): ").strip()
    project_user = input(
        "Enter default user for this project (optional): ").strip()
    project_key = input(
        "Enter default SSH key path for this project (optional): ").strip()
    project_domain = input(
        "Enter default domain for this project (e.g., example.com, optional): ").strip()
    new_project = {"name": project_name, "hosts": []}
    if project_user:
        new_project['user'] = project_user
    if project_key:
        new_project['key'] = project_key
    if project_domain:
        new_project['domain'] = project_domain
    if project_port:
        new_project['port'] = project_port
    backup_config()
    config['projects'].append(new_project)
    if save_config(config):
        print(f"Project '{project_name}' added.")
    else:
        print("Error: Failed to save configuration.")


def edit_project(config):
    print("\n--- Edit Project ---")
    project = select_project(config, prompt="Select a project to edit:")
    if not project:
        return
    print(f"Editing project: {project['name']}")
    new_name = input(
        f"New project name (current: {project['name']}): ").strip()
    if new_name:
        if any(p['name'] == new_name for p in config['projects'] if p is not project):
            print(f"Project with name '{new_name}' already exists.")
            return
        project['name'] = new_name
    new_user = input(
        f"New default user (current: {project.get('user', '')}): ").strip()
    if new_user:
        project['user'] = new_user
    elif 'user' in project and not new_user:
        del project['user']
    new_key = input(
        f"New default key path (current: {project.get('key', '')}): ").strip()
    if new_key:
        project['key'] = new_key
    elif 'key' in project and not new_key:
        del project['key']
    new_domain = input(
        f"New default domain (current: {project.get('domain', '')}): ").strip()
    if new_domain:
        project['domain'] = new_domain
    elif 'domain' in project and not new_domain:
        del project['domain']
    new_port = input(
        f"New default port (current: {project.get('port', '22')}): ").strip()
    if new_port:
        project['port'] = new_port
    elif 'port' in project and not new_port:
        del project['port']
    backup_config()
    if save_config(config):
        print(f"Project {project['name']} updated.")
    else:
        print("Error: Failed to save configuration.")


def delete_project(config):
    print("\n--- Delete Project ---")
    project = select_project(config, prompt="Select a project to delete:")
    if not project:
        return
    confirm = input(
        f"Are you sure you want to delete project '{project['name']}' and all its hosts? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("Project deletion cancelled.")
        return
    backup_config()
    config['projects'] = [p for p in config['projects']
                          if p['name'] != project['name']]
    if save_config(config):
        print(f"Project '{project['name']}' deleted.")
    else:
        print("Error: Failed to save configuration.")


def main_menu():
    while True:
        # Reload config each time to reflect any changes
        config = load_config()
        print("\n--- Host Management Menu ---")
        options = [
            "1. Add New Host",
            "2. Edit Host",
            "3. Delete Host",
            "4. Add New Project",
            "5. Edit Project",
            "6. Delete Project",
            "7. Exit"
        ]
        choice = run_fzf(options, prompt="Choose an action:")
        if not choice:
            print("No action selected.")
            continue
        if choice.startswith("1."):
            add_host(config)
        elif choice.startswith("2."):
            edit_host(config)
        elif choice.startswith("3."):
            delete_host(config)
        elif choice.startswith("4."):
            add_project(config)
        elif choice.startswith("5."):
            edit_project(config)
        elif choice.startswith("6."):
            delete_project(config)
        elif choice.startswith("7."):
            print("Exiting host management.")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main_menu()
