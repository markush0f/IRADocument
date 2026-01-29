# Hierarchical "Tree of Truth" Documentation Strategy

## Conceptual Framework: "The Pyramid of Insight"

This system utilizes a multi-role AI execution strategy to generate high-quality, hierarchical documentation. It moves from atomic code analysis to high-level architectural summaries through three distinct phases.

## Multi-Role Execution Strategy (The Persona Switch)

To ensure purity of context and optimal results, the AI dynamically switches "Personas" (System Prompts) between phases.

### 1. The Miner (Objective Analyst)
*   **Role**: A strict data miner that extracts raw facts without interpreting them.
*   **System Prompt**: "You are a code mining engine. You have NO opinions. You do not summarize. You only extract FACTS using the format: `[IMPACT_LEVEL] TOPIC: Statement`."
*   **Input**: Single Code File.
*   **Output**: JSON List of "Conclusions" (Atomic Facts).
*   **Memory**: Stateless (processes files individually).

### 2. The Architect (Structural Engineer)
*   **Role**: A systems architect that organizes chaos into structure.
*   **System Prompt**: "You are a Systems Architect. You do not read code. You only organize facts. Given a chaotic list of conclusions, build a JSON Tree of Importance. Prioritize architecture over implementation details."
*   **Input**: Aggregated list of all Conclusions from Phase 1.
*   **Output**: Recursive JSON "Importance Tree".
*   **Logic**:
    *   **Roots**: High-impact conclusions.
    *   **Branches**: Supporting details.
    *   **Leaves**: Fine-grained specifics.

### 3. The Scribe (Technical Writer)
*   **Role**: A professional writer that turns structure into prose.
*   **System Prompt**: "You are a Technical Writer. You do not see code. You only see a Concept Tree. Write a cohesive, human-readable documentation page that flows logically from the root concepts down to the details."
*   **Input**: The JSON Importance Tree.
*   **Output**: Final Markdown Documentation.

## Data Structure: The Importance Tree

The intermediate representation is a weighted tree structure:

```json
{
  "root": {
    "topic": "Project Core",
    "children": [
      {
        "topic": "Authentication System",
        "importance": 10,
        "conclusions": ["Uses OAuth2", "Token rotation implemented"],
        "children": [...]
      }
    ]
  }
}
```
