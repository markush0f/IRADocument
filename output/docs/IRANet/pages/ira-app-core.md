# ira/app/core

## Overview

The `ira/app/core` module serves as a foundational component of the project, providing essential services for database management, asynchronous communication, and metrics collection. It facilitates interaction with SQL databases, manages WebSocket connections, and handles the scheduled collection of application metrics, promoting efficient and robust operation.

## File-by-File Analysis

### File: ira/app/extensions/ai_chat/core/initializer.py

- **Purpose**: Implements the chat service's initialization and management features.
- **Key Functions/Classes**:
  - `get_chat_service`: Implements lazy initialization for the `ServerChatService`, constructing it when needed, promoting efficient resource management.
- **Error Handling**: Not specifically mentioned.
- **Dependencies**: Loads tools from a JSON config file located at `app/extensions/ai_chat/tools_calls.json`, and initializes `ModelInterpreter` with a model path specified as `app/extensions/ai_chat/models/qwen2.5-1.5b-instruct-q4_k_m.gguf`.

### File: ira/app/extensions/ai_chat/core/argumen_validator.py

- **Purpose**: Validates arguments based on a defined schema to ensure correct interaction with tools.
- **Key Functions/Classes**:
  - `validate_arguments`: Enforces strict argument validation, including type checks and constraints like 'min' and 'max' for numeric values. Utilizes custom exceptions (`ToolArgumentValidationError`) to handle validation failures.
- **Error Handling**: Raises `ToolArgumentValidationError` for invalid inputs, facilitating robust error management.
- **Dependencies**: Utilizes the `typing` module for type hinting, it promotes clarity within function signatures. 

### File: ira/app/extensions/ai_chat/core/models.py

- **Purpose**: Defines data models ensuring strong validation for parameters used in tool execution.
- **Key Functions/Classes**:
  - `ToolCall`: A class derived from Pydantic's `BaseModel`, it structures data with fields for name and arguments, emphasizing validation and type safety.
- **Error Handling**: Not specifically mentioned.
- **Dependencies**: Uses Pydantic for structured data validation, leveraging `Field()` for metadata handling. 

### File: ira/app/core/sql_loader.py

- **Purpose**: Loads SQL files as text, enabling execution against a database with the provided SQL commands.
- **Key Functions/Classes**:
  - `load_sql`: Reads a SQL file using `Path.read_text`, ensuring content is interpreted with UTF-8 encoding.
- **Error Handling**: Not specifically mentioned.
- **Dependencies**: Imports from `pathlib` for file handling.

### File: ira/app/core/websocket_manager.py

- **Purpose**: Manages WebSocket connections for real-time communication.
- **Key Functions/Classes**:
  - `WebSocketManager`: Handles multiple WebSocket connections using a dictionary, enabling methods to connect, disconnect, and broadcast messages.
- **Error Handling**: The `disconnect` method silently handles non-existent connections without notifying success or failure.
- **Dependencies**: Utilizes FastAPI's WebSocket class for asynchronous handling of connections.

### File: ira/app/core/database.py

- **Purpose**: Establishes database connections and manages sessions asynchronously.
- **Key Functions/Classes**:
  - `get_session()`: Provides a context manager for yielding AsyncSession instances, enabling database access throughout the application.
- **Error Handling**: Not specifically mentioned.
- **Dependencies**: Uses SQLAlchemy's `create_async_engine` and `async_sessionmaker` for database interactions.

### File: ira/app/core/__init__.py

- **Purpose**: This file marks the directory as a Python package.

### File: ira/app/core/application_metrics_scheduler.py

- **Purpose**: Schedules the collection of metrics from applications.
- **Key Functions/Classes**:
  - `application_metrics_scheduler`: Runs every 5 seconds to collect application metrics, using `collect_application_metrics` for data gathering.
- **Error Handling**: Implements logging for exceptions during metric collection, ensuring the process continues uninterrupted.
- **Dependencies**: Integrates `ApplicationMetricsService` for bulk storing metrics into the database via `AsyncSessionLocal`.

## Inter-Module Communication

The `ira/app/core` module interacts with the `ira/app/extensions/ai_chat/core` module, particularly through the use of chat services and tool validation features. Additionally, it communicates with the database and WebSocket components for efficient data handling and real-time user interactions.

## Configuration

Configuration files and paths mentioned include:
- JSON configuration file for tools located at `app/extensions/ai_chat/tools_calls.json`.
- Model path for initialization is found at `app/extensions/ai_chat/models/qwen2.5-1.5b-instruct-q4_k_m.gguf`.

