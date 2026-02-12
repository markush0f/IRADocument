# ira/app/services

## Overview
The `ira/app/services` module provides a suite of services aimed at managing system processes, user systems, and applications. It integrates various functionalities to facilitate efficient system monitoring, user management, and resource tracking across the application.

## File-by-File Analysis

### File: ira/app/services/processes_service.py
#### Purpose
This file provides a class for managing system process snapshots, enhancing resource monitoring capabilities through detailed data aggregation.

#### Key Functions/Classes
- **ProcessesService**: Manages CPU and memory data for real-time process monitoring.
    - **get_process_state**: Obtains the current state of processes.
    - **get_process_memory_res_kb**: Retrieves memory data in kilobytes.
    - **get_processes_table**: Collects data while allowing for limited output based on an optional parameter.
    - **build_processes_header**: Integrates data from multiple modules, generating a comprehensive overview of system metrics.

#### Error Handling
- Exceptions during data collection in `get_processes_table` are logged at the debug level, ensuring robustness without halting execution.

#### Dependencies
- Imports from `app.modules.processes` and `app.modules.system` for process monitoring and system information aggregation.

### File: ira/app/services/user_system_service.py
#### Purpose
Handles user management operations, providing functionality to filter and categorize system users.

#### Key Functions/Classes
- **UsersSystemService**: Retrieves and manages system users.
    - **get_login_allowed_users**: Filters users to exclude those with disallowed login shells.
    - **get_users_summary**: Aggregates detailed summary statistics of all users.
    - **get_active_users**: Fetches currently active users.

#### Dependencies
- Utilizes external user management functions to tie into broader system architectures for tracking user states.

### File: ira/app/services/system/system_alerts_service.py
#### Purpose
Manages system alerts, including persistence and notifications based on monitored metrics.

#### Key Functions/Classes
- **SystemAlertsService**: Handles alerts for critical system thresholds.
    - **notify_critical_alert**: Sends alerts but implements a cooldown mechanism to prevent duplicates.
    - **evaluate_alerts**: Analyzes system metrics to trigger notifications.

#### Error Handling
- Failure in alert persistence is logged to prevent loss of critical alert information.

#### Dependencies
- Leverages a repository for alert handling and notifications via WebSocket.

### File: ira/app/services/system/packages_service.py
#### Purpose
Facilitates retrieval and management of installed packages and their histories.

#### Key Functions/Classes
- **PackagesService**: Manages installed packages and history.
    - **get_packages_paginated**: Retrieves a list of installed packages with pagination.
    - **get_history**: Filters installation history based on specified criteria.

#### Error Handling
- In `get_installed_at`, it returns None without extra logging if a package installation entry is not found.

#### Dependencies
- Relies on external modules for handling operations related to package management.

### File: ira/app/services/system/simple_services_service.py
#### Purpose
Enables discovery of simple services within the system.

#### Key Functions/Classes
- **SimpleServicesService**: Discovers simple services based on user-defined limits.

### File: ira/app/services/system/system_service.py
#### Purpose
Monitors general system resources and manages disk metrics.

#### Key Functions/Classes
- **SystemService**: Aggregates comprehensive system metrics.

### File: ira/app/services/extensions/extension_status_service.py
#### Purpose
Dynamically manages extensions loaded from the filesystem, checking statuses and configurations.

#### Key Functions/Classes
- **ExtensionStatusService**: Gathers status information about installed extensions.

### File: ira/app/services/extensions/extensions_registry.py
#### Purpose
Facilitates dynamic loading and registering of extensions for installation and uninstallation tasks.

#### Key Functions/Classes
- **ExtensionsRegistry**: Manages the registry of extensions, ensuring structured loading and unloading.

### File: ira/app/services/extensions/create_extension_scaffold.py
#### Purpose
Handles the creation of directory structures and files for new extensions.

### File: ira/app/services/collector/application_collector.py
#### Purpose
Collects metrics for various application types dynamically based on their characteristics.

### File: ira/app/services/collector/collect_process_metrics.py
#### Purpose
Acquires detailed CPU and memory metrics from running processes using identifiers.

## Inter-Module Communication
This module interacts with several other modules such as `app.modules.system`, `app.modules.processes`, and extensions modules, allowing for effective integration of user management, system monitoring, and application discovery functionalities.

## Configuration
The module includes several methods with configurable parameters, enabling users to customize various service limits and behaviors. Specific environment configurations were not highlighted in the provided details, but database connectivity might require further setup in practice.

## Related Files

- `ira/app/services/processes_service.py`
- `ira/app/services/user_system_service.py`
- `ira/app/services/system/system_alerts_service.py`
- `ira/app/services/system/packages_service.py`
- `ira/app/services/system/simple_services_service.py`
- `ira/app/services/system/system_service.py`
- `ira/app/services/extensions/extension_status_service.py`
- `ira/app/services/extensions/extensions_registry.py`
- `ira/app/services/extensions/create_extension_scaffold.py`
- `ira/app/services/collector/application_collector.py`
- `ira/app/services/collector/collect_process_metrics.py`
