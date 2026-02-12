# Module Reference

# Module Reference

## Overview
This document serves as a comprehensive reference for the project module, outlining its structure, files, components, and inter-module communication. The documentation provides insights into how the system is organized and how various components interact with each other.

## File-by-File Analysis

### File: LICENSE
- **Purpose:** The software is licensed under the MIT License, allowing users to use, copy, modify, merge, publish, distribute, sublicense, and sell the Software without restrictions, while disallowing warranties or liabilities for damages.

### File: ira/proccess.py
- **Purpose:** Process Management and Output Handling.
- **Key Functions:**
  - Imports `scan_processes` from `app.modules.scanner.process`, leveraging it to iterate through process instances with an execution time of at least 15 seconds, highlighting filtering based on process lifetime.
- **Dependencies:** Relies on the `app.modules.scanner.process` module, emphasizing a dependency that encapsulates process scanning functionality.
- **Output Handling:** Prints details of processes including `pid`, `comm`, `etimes`, `cwd`, and a truncated `cmdline`, providing essential runtime information for monitoring and debugging activities.

### File: ira/Dockerfile
- **Purpose:** Environment Configuration for Docker.
- **Key Aspects:**
  - Sets environment variables `PYTHONDONTWRITEBYTECODE` and `PYTHONUNBUFFERED` to improve Python performance.
  - Uses `python:3.12-slim` as the base image, ensuring a lightweight and optimized environment tailored for web applications.
  - Installs essential packages via `apt-get`, including `build-essential` and `libpq-dev` which are critical for building Python packages with native extensions.
  - Sets the working directory to `/app` for consistent context in subsequent commands.
  - Copies the `requirements.txt` file and the application code ensuring dependencies and source code are included.
  - Exposes port 8000 for Uvicorn application to listen, facilitating external access for web requests.
  - Specifies the command to run the application using Uvicorn, pointing to `app.main:app`.

### File: ira/app/main.py
- **Purpose:** Lifecycle Management and Configuration Management.
- **Key Functions:**
  - Uses an async context manager for lifespan to manage long-running tasks like metrics scheduling and database connections.
  - Conditionally includes an AI chat extension router based on `ExtensionsService` which checks if the `ai_chat` extension is enabled.
  - Configures CORS middleware to allow all origins, methods, and headers.
  - Schedules two background tasks: `metrics_scheduler()` and `application_metrics_scheduler()` to handle asynchronous metrics collection.
  - Implements structured logging for debugging and monitoring using `app.core.logger`.
  - Handles application configuration via a dedicated `load_config()` function, accessible through the `/config` endpoint.
  - Employs async context managers for error handling ensuring tasks are canceled on shutdown to prevent resource leaks.
  - Manages database sessions using a context manager `get_session()` for efficient dependency injection.

### File: ira/app/repositories/applications.py
- **Purpose:** Database Operations.
- **Key Components:**
  - The `ApplicationRepository` class utilizes SQLAlchemy's `AsyncSession` for asynchronous operations, enhancing responsiveness and scalability.
  - Supports CRUD operations directly manipulating the Application model.
  - Includes robust error handling in `update_runtime_state` for checking application existence.
  - Dynamically sets `created_at` and `last_seen_at` using `datetime.now(timezone.utc)`.
  - Constructs conditional queries through `applications_with_path_logs` to filter applications based on related entities.

### File: ira/app/repositories/application_metrics_repository.py
- **Purpose:** Data Management for Application Metrics.
- **Key Components:**
  - The `ApplicationMetricssRepository` class uses `AsyncSession` for asynchronous data operations.
  - The `insert()` and `insert_many()` methods commit changes to the database after inserting metrics instances.
  - Methods `list_by_application()` and `list_latest_by_application()` retrieve metrics based on application_id and predefined limits.

### File: ira/app/repositories/system_alerts.py
- **Purpose:** Management of System Alerts.
- **Key Components:**
  - `SystemAlertRepository` uses `AsyncSession` for non-blocking database operations.
  - The `insert_critical` method creates alert instances based on parameters like `host`, `metric`, and `level`.
  - All interactions are asynchronous, improving performance under load.
  - Explicit error handling is absent during database commits, potentially leading to unhandled exceptions.

### File: ira/app/repositories/logs.py
- **Purpose:** Data Access for Application Logs.
- **Key Components:**
  - `ApplicationLogRepository` uses `AsyncSession` for queries ensuring non-blocking behavior.
  - Methods `list_for_application()` and `list_active_base_paths()` retrieve applications logs based on filtering conditions.
  - The `insert()` method creates structured logs with attributes like `application_id`, `base_path`, and associated timestamps.
  - Current implementation lacks error handling for potential integrity errors during database interactions.

### File: ira/app/modules/system/commands.py
- **Purpose:** Command Execution in the System.
- **Key Functions:**
  - The `run_command` function utilizes `subprocess.run` for executing commands, capturing outputs systematically.
  - Implements robust error handling for command execution failures and returns standardized dictionary outputs.
  - Depends on the `subprocess` library for executing commands.

### File: ira/app/modules/system/users.py
- **Purpose:** User Management. 
- **Key Functions:**
  - Processes user details from `PASSWD_FILE`, categorizing as 'human' or 'system'.
  - Methods identify and filter active users, handle group membership with error handling, and detect inactive human users based on logged-in status.

### File: ira/app/modules/system/proc.py
- **Purpose:** Process Management.
- **Key Functions:**
  - Retrieves command line arguments using `read_process_cmdline`, uptime with `read_uptime_seconds`, and lists process IDs through `list_pids()`.
  - Functions handle exceptions gracefully, returning default values without crashing the application.

### File: ira/app/modules/scanner/process.py
- **Purpose:** Scanning Processes.
- **Key Functions:**
  - `scan_processes` retrieves and filters process IDs based on specific criteria.
  - Functions check command eligibility and compute time elapsed since process initiation.

### File: ira/app/services/processes_service.py
- **Purpose:** Process Management Service.
- **Key Functions:**
  - Provides snapshots of system processes and structures data for UI updates.
  - Handles errors in process data logging robustly, integrates with various modules for comprehensive monitoring.

### File: ira/app/api/applications.py
- **Purpose:** API Design for Applications.
- **Key Features:**
  - Defines FastAPI endpoints for CRUD operations on applications using dependency injection for table access.
  - Implements error handling through HTTPExceptions for clear client feedback on operations.

### File: ira/app/api/health.py
- **Purpose:** Health Check Endpoint.
- **Key Features:**
  - The `/health` endpoint provides a simple status indication, returning {'status': 'ok'}. This is useful for uptime monitoring.

### Inter-Module Communication
This module interacts with various components within the application through dependency injection, enabling efficient service management and resource access. Key interactions include:
- The integration of application services like `ApplicationsService`, `UsersSystemService`, and others for centralized functionality.
- API routes facilitated by FastAPI ensure modular access to services, centralized error handling, and structured responses for frontend communication.

### Configuration
- **Environment Variables:** The system relies on configuration files, such as `ira.config.json`, to set critical paths and service integration levels.
- **Default Values:** The software defaults host configurations in the API for frontend services, illustrating the importance of extensible configuration for deployment flexibility.

### Conclusion
This documentation provides a foundation for understanding the structure and functionality of the project modules, emphasizing the importance of modular design and inter-service communication within the system architecture.