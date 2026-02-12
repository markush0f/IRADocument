# ira/app/extensions/iraterm/host

## Overview

The `ira/app/extensions/iraterm` module provides functionalities for managing an integrated terminal environment, consisting of backend services, frontend interfaces, and system services. It encompasses the backend server that operates on a defined port for WebSocket communication, a frontend developed with React for user interaction, and the necessary scripts for installation and uninstallation of the service components. This documentation specifically focuses on the `host` portion of the module which is responsible for uninstalling services associated with the terminal functionalities.

## File-by-File Analysis

### File: `ira/app/extensions/iraterm/host/uninstall_services.py`
- **Purpose**:
  - The script is designed to stop and disable relevant system services associated with the iraterm application, ensuring that all dependencies and units are properly removed from the system.

- **Key Functions**:
  - **_require_root**: Enforces that the script is run with root privileges by checking the effective user ID. If not executed as root, the script will exit to prevent unauthorized changes.

- **Service Management**:
  - The script utilizes `systemctl` commands to stop and disable the services named `iranet-iraterm-frontend.service` and `iranet-iraterm-backend.service`, ensuring they are no longer active and preventing potential conflicts or lingering resource usage.

- **File Management**:
  - It removes the service unit files pertaining to both the frontend and backend, utilizing `unlink` on their respective `Path` objects, which point to their locations in `/etc/systemd/system`.
  
- **Daemon Reload**:
  - After stopping services and removing unit files, the script invokes `systemctl daemon-reload` to refresh the systemd manager configuration. This action ensures that any changes made to the service states take effect immediately.

## Inter-Module Communication

- The module interacts with other components of the iraterm system to check and terminate services that are no longer needed. Specifically, it addresses frontend and backend services directly managed through systemd, enabling seamless management and operability of the entire terminal environment.

## Configuration

- **Root Privileges**:
  - The execution of the uninstall script requires the user to have root privileges to manage system services, ensuring security and proper access controls when making changes to service states.

- **Service Unit Files**:
  - The script removes specific service unit files located in `/etc/systemd/system`, which are essential for managing the installed services of the iraterm module. Cleaning these files is vital for maintaining an uncluttered system state after uninstallation.

## Summary

The `uninstall_services.py` script in the `ira/app/extensions/iraterm/host` module plays a critical role in the lifecycle management of the iraterm application by managing the removal of system services. It ensures that necessary permissions are respected, services are properly terminated, and system configurations are updated accordingly, leaving the system in a clean state post-uninstallation.