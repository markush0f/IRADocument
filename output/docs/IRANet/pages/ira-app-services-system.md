# ira/app/services/system/system_service.py

# File: ira/app/services/system/system_service.py

## Purpose
The `system_service.py` file defines the `SystemService` class, which is used for monitoring various system resources and metrics.

## Key Functions/Classes
### SystemService
- **SystemService**: Monitors system resources with several methods to provide insight into system performance.
  - **build_system_snapshot**: Gathers critical metrics including uptime, memory, and CPU usage.
  - **get_system_disk**: Collects and formats disk usage from system partitions.
  - **build_system_alerts_snapshot**: Generates flags for system load conditions against CPU core counts.

### Error Handling
The `_resolve_status` method categorizes disk usage based on defined thresholds for efficient health management of the disks.

## Dependencies
Relies on specific functions from the `app.modules.system` package for metric aggregation.