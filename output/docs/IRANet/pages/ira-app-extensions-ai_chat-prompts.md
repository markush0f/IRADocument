# ira/app/extensions/ai_chat/prompts

## Overview
The `ira/app/extensions/ai_chat/prompts` module is designed to manage the prompts used in the AI Chat extension of the application. It defines structures and formats necessary for the AI assistant to understand the context in which it operates and generate responses based on the specified input.

## File-by-File Analysis

### File: ira/app/extensions/ai_chat/prompts/prompts.py
- **Purpose**: This file handles the definition of prompt structures used in the AI Chat extension. It ensures that the system can maintain a clear and consistent interaction style.
- **Key Variables**:
  - `DEFAULT_SYSTEM_PROMPT`: This variable defines a strict JSON output structure for a server monitoring assistant. This structure prohibits additional text, explanations, or examples to ensure that responses are concise and machine-readable, which is vital for effective communication in server monitoring tasks.
- **Error Handling**: Error handling specifics are not detailed within this module, suggesting that any errors arising from invalid prompt structures would need to be managed at higher levels of the application where these prompts are utilized.
- **Dependencies**: The module does not explicitly mention any external dependencies.

## Inter-Module Communication
The `prompts` module interfaces with other components of the AI Chat extension wherever prompts are required. This could include communication with service layers that process interactions based on prompts, ensuring the assistant responds appropriately based on the structured output defined here.

## Configuration
Configuration specifics for this module are limited to the definition of the `DEFAULT_SYSTEM_PROMPT`, which enforces constraints on how the system interacts with its users and how outputs are formatted to maintain consistency across responses.