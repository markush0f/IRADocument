# Module Reference: ira/app/extensions/ai_chat/migrations

## Overview
This module is part of the AI chat extension, specifically responsible for managing database migrations required for the extension's functionality. It handles changes to the database schema essential for the features provided by the AI chat system, particularly concerning chat messages and their formats.

## File-by-File Analysis

### File: ira/app/extensions/ai_chat/migrations/999_drop.sql
- **Database Migration**: This SQL migration script drops the tables `ai_chat_messages` and `ai_chats` if they exist, indicating significant schema alterations related to the AI chat extension. This may be necessary for clean-up or re-structuring of the database related to chat functionalities.

### File: ira/app/extensions/ai_chat/migrations/002_add_message_formats.sql
- **Database Schema**: This migration script modifies the `ai_chat_messages` table by adding two columns: `content_json` for storing JSON formatted content and `content_markdown` for Markdown formatted content. This enhancement allows for greater flexibility in the types of content that can be stored within chat messages, catering to a variety of data presentation needs.

## Inter-Module Communication
The migrations module does not explicitly communicate with other modules; however, it indirectly supports the functionality of the AI chat extension and relies on correct implementation and execution of the migrations to ensure the AI chat features operate with the intended database schema.

## Configuration
No specific configuration details are outlined in the migrations module documentation. It is implied that the migrations depend on the existence of required database structures and schemas as managed via the migration scripts.

## Related Files

- `ira/app/extensions/ai_chat/install.py`
- `ira/app/extensions/ai_chat/tools_calls.json`
