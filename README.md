# IRADocument

**AI-Powered Code Documentation & Analysis Engine**

IRADocument is an intelligent documentation system that automatically analyzes code repositories and generates comprehensive, structured documentation using advanced AI agents. It extracts technical insights, API endpoints, architecture patterns, and creates wiki-style documentation without manual intervention.

## 🌟 Features

### 🤖 AI-Powered Analysis
- **Universal Language Support**: Analyzes code in any programming language (Python, JavaScript, Go, Java, Ruby, PHP, Rust, etc.)
- **Framework Agnostic**: Detects and understands any framework automatically (FastAPI, Spring, Django, Rails, Express, Phoenix, etc.)
- **Smart Pattern Recognition**: Identifies architectural patterns, API endpoints, and relationships without hardcoded rules

### 📚 Documentation Generation
- **Triad Agent Architecture**: 
  - **Miner**: Extracts atomic facts from source code
  - **Architect**: Plans documentation structure and detects subsystems
  - **Scribe**: Writes detailed, technical documentation pages
- **Hierarchical Navigation**: Generates organized sidebar structure based on project architecture
- **Mermaid Diagrams**: Automatically creates visual diagrams for complex flows

### 🔍 Code Analysis
- **Technology Stack Detection**: Identifies frameworks, libraries, databases, and tools
- **API Endpoint Extraction**: Finds all HTTP routes across any framework or language
- **Project Tree Visualization**: Generates file structure for frontend rendering
- **Subsystem Detection**: Identifies backend, frontend, CLI, infrastructure components

### 🎯 Smart Processing
- **AI-Driven File Selection**: Uses AI to pick relevant files for analysis (not hardcoded filters)
- **Batch Processing**: Analyzes multiple files in parallel with rate limiting
- **Token Management**: Intelligent truncation to stay within context limits
- **Async Operations**: Non-blocking I/O for scalable performance

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     FastAPI Backend                      │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌───────────┐  ┌────────────┐  ┌──────────────┐       │
│  │   Miner   │→ │ Architect  │→ │    Scribe    │       │
│  │  Agent    │  │   Agent    │  │    Agent     │       │
│  └───────────┘  └────────────┘  └──────────────┘       │
│       ↓              ↓                  ↓                │
│  ┌───────────────────────────────────────────┐          │
│  │         LLM Factory (OpenAI/Ollama)       │          │
│  └───────────────────────────────────────────┘          │
│                                                           │
│  ┌───────────────────────────────────────────┐          │
│  │  Services: Analysis, Documentation,       │          │
│  │  Endpoint Extraction, File Tree           │          │
│  └───────────────────────────────────────────┘          │
│                                                           │
│  ┌───────────────────────────────────────────┐          │
│  │  Storage: SQLModel + SQLite/PostgreSQL    │          │
│  └───────────────────────────────────────────┘          │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Git
- OpenAI API Key (or Ollama for local LLMs)

### Installation

```bash
# Clone the repository
git clone https://github.com/markush0f/IRADocument.git
cd IRADocument

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY='your-api-key-here'
export IRA_OPENAI_API_KEY='your-api-key-here'  # Alternative env var

# Run the server
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## 📖 API Endpoints

### Core Analysis

#### **POST** `/clone`
Clone a Git repository for analysis.

```json
{
  "repo_url": "https://github.com/user/project",
  "branch": "main"
}
```

#### **POST** `/pipeline/analyze`
Run basic analysis pipeline (tech stack, file structure).

```json
{
  "repo_url": "https://github.com/user/project",
  "branch": "main"
}
```

#### **POST** `/analysis/tech-stack`
Analyze and detect all technologies used in the project.

```json
{
  "repo_url": "https://github.com/user/project",
  "branch": "main"
}
```

### Documentation Generation

#### **POST** `/documentation/generate`
Generate full AI-powered documentation using the Triad (Miner → Architect → Scribe).

```json
{
  "repo_url": "https://github.com/user/project",
  "branch": "main"
}
```

**Response:**
```json
{
  "project_id": "abc123",
  "status": "completed",
  "docs_path": "wiki_docs/abc123/",
  "total_pages": 15,
  "pages": [
    {"id": "backend-overview", "status": "success"},
    {"id": "api-reference", "status": "success"}
  ]
}
```

### Endpoint Extraction

#### **POST** `/analysis/endpoints`
Extract all API endpoints using AI (framework-agnostic).

```json
{
  "repo_url": "https://github.com/user/api-project",
  "branch": "main"
}
```

**Response:**
```json
{
  "project_id": "abc123",
  "count": 12,
  "endpoints": [
    {
      "method": "GET",
      "path": "/users",
      "file_path": "routes/users.py",
      "line_number": 45,
      "description": "Fetch all users"
    }
  ]
}
```

### File Structure

#### **POST** `/analysis/tree`
Get the complete file tree structure (no AI, pure filesystem scan).

```json
{
  "repo_url": "https://github.com/user/project",
  "branch": "main"
}
```

**Response:**
```json
{
  "project_id": "abc123",
  "repo_url": "https://github.com/user/project",
  "tree": {
    "name": "repo",
    "type": "directory",
    "children": [
      {
        "name": "src",
        "type": "directory",
        "children": [...]
      },
      {
        "name": "README.md",
        "type": "file"
      }
    ]
  }
}
```

## 🎨 Agent System

### The Triad Architecture

IRADocument uses a three-agent pipeline inspired by knowledge extraction and synthesis workflows:

#### 1. **Miner Agent** 🔍
- **Role**: Extract atomic facts from source code
- **Output**: List of conclusions (topic, impact, statement)
- **Philosophy**: "I don't understand the whole. I only see the piece. But I see it clearly."
- **Prompt**: Focuses on HOW and WHY, not just WHAT

**Example Output:**
```json
{
  "file": "auth/service.py",
  "conclusions": [
    {
      "topic": "Security",
      "impact": "HIGH",
      "statement": "Implements OAuth2 Password Bearer flow using python-jose for JWT encoding with HS256 algorithm."
    }
  ]
}
```

#### 2. **Architect Agent** 🏛️
- **Role**: Plan documentation structure
- **Tasks**: 
  - Detect subsystems (backend, frontend, CLI, infrastructure)
  - Design hierarchical navigation tree
  - Map modules to documentation pages
- **Output**: Wiki navigation structure with categories and pages

**Example Output:**
```json
{
  "project_name": "MyAPI",
  "detected_subsystems": ["backend", "frontend"],
  "tree": [
    {
      "id": "backend-api",
      "label": "Backend API",
      "type": "category",
      "children": [
        {"id": "backend-overview", "label": "Overview", "type": "page"}
      ]
    }
  ]
}
```

#### 3. **Scribe Agent** ✍️
- **Role**: Write detailed technical documentation
- **Types**: Architecture overviews and module references
- **Output**: Markdown content with diagrams
- **Features**: Verbose, technical, professional developer-to-developer tone

## ⚙️ Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...                    # OpenAI API key
IRA_OPENAI_API_KEY=sk-...               # Alternative key name

# Optional
IRA_OLLAMA_BASE_URL=http://localhost:11434  # Ollama server (if using local LLM)
LOG_LEVEL=INFO                           # Logging level
DATABASE_URL=sqlite:///./ira_document.db # Database connection
```

### Configuration File

Edit `app/core/config.py` to customize:
- LLM provider (OpenAI/Ollama)
- Model selection (gpt-4o-mini, gpt-4, etc.)
- Logging preferences
- Database settings

## 📁 Project Structure

```
IRADocument/
├── app/
│   ├── agents/              # AI Agents
│   │   ├── miner/          # Fact extraction agent
│   │   ├── architect/      # Documentation planning agent
│   │   ├── scribe/         # Content writing agent
│   │   ├── extractor/      # Endpoint extraction prompts
│   │   ├── core/           # Base classes and LLM clients
│   │   └── tools/          # Tool registry for agents
│   ├── models/             # Database models (SQLModel)
│   ├── services/           # Business logic services
│   ├── pipeline/           # Analysis pipeline steps
│   ├── scanners/           # Technology detection scanners
│   ├── core/               # Config, logger, database
│   └── main.py             # FastAPI application
├── scripts/                # Standalone scripts
├── tests/                  # Test suite
├── wiki_docs/              # Generated documentation output
└── requirements.txt
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/agents/miner/test_miner.py
```

## 🛠️ Development

### Adding a New Agent

1. Create directory: `app/agents/your_agent/`
2. Define prompts: `prompts.py`
3. Define schema: `schema.py` (Pydantic models)
4. Implement agent: `agent.py`
5. Register tools if needed

### Adding a New Scanner

1. Create scanner: `app/scanners/your_scanner.py`
2. Implement detection logic
3. Add to `TechnologyScanner` orchestrator

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style

- All code must be in **English** (including comments)
- Follow PEP 8 for Python
- Use type hints
- Write tests for new features

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for GPT models
- FastAPI framework
- SQLModel for elegant database handling
- The open-source community

## 📧 Contact

**Markus** - [@markush0f](https://github.com/markush0f)

Project Link: [https://github.com/markush0f/IRADocument](https://github.com/markush0f/IRADocument)

---

**Made with ❤️ and AI**
