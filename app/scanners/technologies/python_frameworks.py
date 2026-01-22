"""Framework metadata for Python scanning."""

FRAMEWORK_DEPENDENCIES = {
    "django": {"django"},
    "flask": {"flask"},
    "fastapi": {"fastapi"},
    "pyramid": {"pyramid"},
    "bottle": {"bottle"},
    "tornado": {"tornado"},
    "aiohttp": {"aiohttp"},
    "pandas": {"pandas"},
    "numpy": {"numpy"},
    "scikit-learn": {"scikit-learn"},
    "tensorflow": {"tensorflow"},
    "pytorch": {"torch"},
    "celery": {"celery"},
    "sqlalchemy": {"sqlalchemy"},
    "pydantic": {"pydantic"},
    "pytest": {"pytest"},
    "scrapy": {"scrapy"},
    "streamlit": {"streamlit"},
    "dash": {"dash"},
}

FRAMEWORK_CONFIGS = {
    "django": {"manage.py"},
    "scrapy": {"scrapy.cfg"},
    "streamlit": {
        ".streamlit/config.toml"
    },  # Often a directory, but file matching is usually by name
}
