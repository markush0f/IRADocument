# ira/app/modules/system

## Overview
The `system` module provides functionalities related to operating system interactions, user management, process management, and system services, facilitating diverse operations necessary for managing a Linux-based system.

## File-by-File Analysis

### File: ira/app/modules/system/commands.py
#### Purpose
This file encapsulates functionalities for executing external commands and handling their results in a standardized manner.

#### Key Functions/Classes
- **run_command**: Executes external commands using `subprocess.run`, capturing stdout, stderr, and exit status with structured output for robust error handling. It returns a dictionary containing keys 'ok', 'stdout', and 'stderr'.

#### Error Handling
Handles errors robustly by catching `FileNotFoundError` for unavailable commands and `subprocess.CalledProcessError` for execution failures, providing informative responses through standardized dictionary outputs.

#### Dependencies
Relies on the `subprocess` library for command execution, requiring a list of strings as input for commands for enhanced modularity and reusability.

### File: ira/app/modules/system/types.py
#### Purpose
This file defines structured type definitions to maintain type safety across the codebase.

#### Key Functions/Classes
- **DiskPartition** and **DiskProcessUsage**: Defined as `TypedDicts`, they provide structured and safe data representations for disk partitions and processes, ensuring clarity in data handling.

#### Data Typing
Utilizes `TypedDict` from the typing module, explicitly defining necessary properties and types.

### File: ira/app/modules/system/users.py
#### Purpose
This module focuses on user management by handling user details and their system activity.

#### Key Functions/Classes
- **system_users**: Processes user information from the `PASSWD_FILE`, categorizing users into 'human' and 'system' types based on UID.
- **active_users**: Retrieves currently logged-in users, filtering results from `system_users` to return active accounts.
- **sudo_users**: Returns users who belong to the 'sudo' group, with error handling for potential absence of this group.
- **unused_users**: Identifies human users not currently logged in, enhancing user management by flagging inactive accounts.

#### Error Handling
The `sudo_users` function gracefully manages the absence of the 'sudo' group by catching `KeyError`, returning an empty list in such cases.

### File: ira/app/modules/system/proc.py
#### Purpose
This file handles process management and related metrics retrieval.

#### Key Functions/Classes
- **read_process_cmdline**: Retrieves command line arguments for a specified process by reading from `/proc/<pid>/cmdline`.
- **read_uptime_seconds**: Reads system uptime in seconds from `/proc/uptime`. 
- **list_pids**: Lists all active process IDs by checking the `/proc` directory's contents.
- **read_process_cwd**: Retrieves the current working directory for a specified process.

#### Error Handling
Functions return default values on exceptions during filesystem access, ensuring applications don't crash.

#### Dependencies
Utilizes the Linux `/proc` filesystem for process-related data access.

### File: ira/app/modules/system/nginx.py
#### Purpose
Manages Nginx service operations, including status checks and reload commands.

#### Key Functions/Classes
- **get_nginx_status**: Checks the Nginx service status using `systemctl`, with a fallback mechanism to `nginx -t` if necessary.
- **reload_nginx**: Reloads the Nginx service, trying both `systemctl reload` and `nginx -s reload` as backups.

#### Error Handling
Utilizes structured logging to capture successful operations and failures, logging messages for easier troubleshooting.

#### Dependencies
Relies on the `run_command` function from `commands.py` to execute system commands.

## Inter-Module Communication
Modules communicate extensively within the system architecture, particularly `commands.py` which serves as a utility for executing system commands across various functionalities in this module.

## Configuration
No specific environment variables are indicated, but there are dependencies on system file paths such as `/proc`, `/var/log/apt`, and user/group database files for operations.