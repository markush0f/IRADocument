# Directories to skip during source code collection
SKIP_DIRS = {
    "node_modules",
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    "dist",
    "build",
    ".next",
    ".nuxt",
    ".output",
    ".cache",
    ".turbo",
    "coverage",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".idea",
    ".vscode",
    "tmp",
    "temp",
    "logs",
    "public",
    "assets",
    "static",
    "vendor",
    "target",
    ".gradle",
    ".cargo",
    "bin",
    "obj",
}

# File extensions to ignore (binary, lockfiles, media, non-code text)
IGNORE_EXTENSIONS = {
    # Lockfiles and generated
    ".lock",
    ".json-lock",
    ".map",
    ".log",
    # Text documentation (not source code)
    ".md",
    ".txt",
    ".rst",
    ".csv",
    # Images
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".ico",
    ".webp",
    ".bmp",
    ".tiff",
    # Fonts
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".otf",
    # Media
    ".mp4",
    ".mp3",
    ".wav",
    ".avi",
    ".mov",
    ".webm",
    # Archives
    ".zip",
    ".tar",
    ".gz",
    ".bz2",
    ".7z",
    ".rar",
    # Compiled / binary
    ".pyc",
    ".pyo",
    ".class",
    ".o",
    ".obj",
    ".dll",
    ".exe",
    ".so",
    ".dylib",
    ".a",
    ".lib",
    ".jar",
    ".war",
    ".wasm",
    # Documents
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    # Minified files
    ".min.js",
    ".min.css",
    # Database files
    ".db",
    ".sqlite",
    ".sqlite3",
    # Environment
    ".env",
    ".env.local",
}

# Filenames to always ignore regardless of extension
IGNORE_FILENAMES = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "Pipfile.lock",
    "composer.lock",
    "Cargo.lock",
    "Gemfile.lock",
    ".DS_Store",
    "Thumbs.db",
    ".gitattributes",
    ".editorconfig",
    ".prettierrc",
    ".eslintcache",
}

# Maximum file size in bytes before skipping (100KB)
MAX_FILE_SIZE_BYTES = 100_000

# Hard limit on number of files to collect
MAX_FILES_LIMIT = 300

# Cost per million input tokens by provider/model (USD)
# These are approximate and should be updated as pricing changes
COST_PER_MILLION_INPUT_TOKENS = {
    # OpenAI
    "gpt-4o": 2.50,
    "gpt-4o-mini": 0.15,
    "gpt-4-turbo": 10.00,
    "gpt-3.5-turbo": 0.50,
    # Gemini
    "gemini-1.5-flash": 0.075,
    "gemini-1.5-flash-8b": 0.0375,
    "gemini-1.5-pro": 1.25,
    "gemini-2.0-flash": 0.10,
    "gemini-pro-latest": 0.50,
    # Ollama (local, free)
    "ollama": 0.0,
}

# Cost per million output tokens by provider/model (USD)
COST_PER_MILLION_OUTPUT_TOKENS = {
    # OpenAI
    "gpt-4o": 10.00,
    "gpt-4o-mini": 0.60,
    "gpt-4-turbo": 30.00,
    "gpt-3.5-turbo": 1.50,
    # Gemini
    "gemini-1.5-flash": 0.30,
    "gemini-1.5-flash-8b": 0.15,
    "gemini-1.5-pro": 5.00,
    "gemini-2.0-flash": 0.40,
    "gemini-pro-latest": 1.50,
    # Ollama (local, free)
    "ollama": 0.0,
}

# Default safety limit for maximum estimated cost (USD)
DEFAULT_MAX_COST_USD = 1.00

# Miner concurrency and rate control
MINER_CONCURRENCY_LIMIT = 3
MINER_RATE_DELAY_SECONDS = 1.5

# Token limits for truncation
MINER_MAX_TOKENS_PER_FILE = 3000
SCRIBE_MAX_INPUT_TOKENS = 100_000
