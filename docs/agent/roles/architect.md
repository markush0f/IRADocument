# Role: The Architect

## Philosophy
The Architect is the **Structural Layer**. While the Miner sees pixels, the Architect sees the image. 
Its job is **Synthesis and Hierarchy**. It does not look at the code; it trusts the Miner's facts implicitly.

> "Data without structure is noise. My job is to build the skeleton of understanding."

## Responsibilities
1.  **Ingest** the chaotic pile of "Conclusions" from hundreds of files.
2.  **Cluster** related facts by topic (e.g., grouping "JWT", "OAuth", "Login" under "Authentication").
3.  **Weigh** the clusters. Which topics have the most "High Impact" facts? These become the **Root Nodes**.
4.  **Structure** the tree.
    *   **Roots**: Major Architectural pillars.
    *   **Branches**: Implementation strategies.
    *   **Leaves**: Specific details (file-level facts).

## The "Big Picture" Rule
The Architect prioritizes **Breadth over Depth**.
*   *Bad*: Creating a root node for a specific utility function just because it's complex.
*   *Good*: Creating a root node for "Data Ingestion" because 50 files contribute to it.

## Input/Output Contract

### Input
*   **List of Conclusions**: A massive JSON array containing every fact extracted by the Miners from all files.

### Output (The Importance Tree)
```json
{
  "project_roots": [
    {
      "topic": "Authentication",
      "weight": 85, // Calculated based on number/impact of facts
      "summary_intent": "The system uses a dual-token strategy with Redis backing.",
      "children": [
        {
          "topic": "Token Management",
          "weight": 40,
          "facts": [
            "Tokens signed with RS256", 
            "Expiration fixed at 15m"
          ] 
        }
      ]
    },
    {
      "topic": "Infrastructure",
      "weight": 60,
      "children": [...]
    }
  ]
}
```

## Prompt Strategy
The Architect's prompt must force it to:
*   **Discard** noise (facts that don't fit a pattern).
*   **Rename** topics for clarity (e.g., merging "Auth" and "Login" into "Authentication").
*   **Enforce** a maximum depth (e.g., 3 levels) to prevent infinite complexity.
