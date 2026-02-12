# ira/app/models/entities

## Overview

The `ira/app/models/entities` module is responsible for defining various data models that interact with a database. These models are designed to provide structured representations of applications, metrics, logs, and alerts, ensuring that all data adheres to defined formats and integrity constraints. The models integrate with SQLModel, which streamlines ORM functionalities, allowing for efficient database operations and validations.

## File-by-File Analysis

### File: ira/app/models/entities/extension.py
- **Purpose**: The `Extensions` class maps to a database table and represents extensions that the application can manage.
- **Key Functions/Classes**:  
  - **Extensions Class**: Inherits from `SQLModel` and utilizes fields defined by `Field` for ORM.
  - **Primary Key**: The `id` field serves as the primary key, ensuring uniqueness.
  - **Default Values**: `created_at` is auto-populated with the current UTC time upon creation.
  - **Boolean Configuration**: The `enabled` field has a default value of `False`, indicating whether the extension is active.
- **Error Handling**: Not explicitly mentioned, so no error handling mechanisms are defined.
- **Dependencies**: Depends on `SQLModel` for ORM capabilities.

### File: ira/app/models/entities/application_metrics.py
- **Purpose**: The `ApplicationMetrics` class stores application performance metrics in the database.
- **Key Functions/Classes**:  
  - **ApplicationMetrics Class**: Defines various fields including `application_id`, timestamps, CPU percentage, and memory usage.
  - **Foreign Key Relationship**: The `application_id` field references `applications.id` to maintain data integrity.
  - **Field Configuration**: Uses `SQLModel`'s `Field` and SQLAlchemy's `Column` for defining database characteristics and constraints.
- **Error Handling**: Indicates non-nullability on essential fields but lacks explicit handling mechanisms for database operations.
- **Dependencies**: Utilizes `SQLModel` and `SQLAlchemy` for ORM and database interactions.

### File: ira/app/models/entities/application_log.py
- **Purpose**: Represents a log path for applications in the database, tracking where logs are stored.
- **Key Functions/Classes**:  
  - **ApplicationLogPath Class**: Ensures no duplicate paths due to unique constraints on `application_id` and `base_path`.
  - **Data Integrity**: Fields `enabled` and `discovered` manage the log path status.
  - **Timestamps**: The `created_at` field is set using a callable function to record the time of creation.
  - **UUID Usage**: Both `id` and `application_id` make use of UUIDs to enhance uniqueness.
- **Error Handling**: Not specified, thus no mechanisms are mentioned for error handling.
- **Dependencies**: Relies on `SQLModel` for ORM functionality.

### File: ira/app/models/entities/system_alert.py
- **Purpose**: Defines a model for managing system alerts, capturing critical monitoring metrics.
- **Key Functions/Classes**:  
  - **SystemAlert Class**: Includes fields for `id`, `host`, `metric`, and `thresholds` to define alert parameters.
  - **Database Integration**: Functions with SQLModel, facilitating ORM capabilities and data interactions.
  - **Field Configuration**: Mandatory fields `first_seen_at` and `last_seen_at` ensure key timing information is recorded.
  - **Default Values**: The `resolved_at` field is defaulted to None, denoting unresolved alerts.
- **Error Handling**: No specific error handling mentioned for the model operations.
- **Dependencies**: Integrates with `SQLModel` for database interaction.

## Inter-Module Communication

This module interfaces with the `ira/app/models/dto` module where data transfer objects (DTOs) such as `ApplicationCollectedMetricsDTO`, `SystemPackages`, and various others are utilized. The use of Pydantic for DTOs indicates a reliance on structured data representation, enhancing the communication between different layers of the application.

## Configuration
- The module does not explicitly define any environment variables, constants, or defaults beyond the specified data models and their field defaults. However, the models include automatic population and default values such as for `created_at` fields and boolean flags, which facilitate the tracking and behavior of the entities within the database.