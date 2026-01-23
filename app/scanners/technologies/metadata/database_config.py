"""Database file patterns."""

# Binary/Embedded database files
BINARY_DB_EXTENSIONS = {
    ".sqlite",
    ".sqlite3",
    ".db",
    ".db3",
    ".s3db",
    ".sl3",
    ".mdb",  # Access
    ".accdb",  # Access
    ".fdb",  # Firebird
    ".gdb",  # InterBase
    ".rdb",  # Redis dump (sometimes)
    ".odb",  # OpenOffice Base
}

# Database scripts/dumps
SCRIPT_DB_EXTENSIONS = {
    ".sql",
    ".psql",
    ".mysql",
    ".pgsql",
    ".dump",
}

# ORM and Migration Configuration files
CONFIG_FILES = {
    # Python / Alembic / SQLAlchemy
    "alembic.ini",
    # Node / Sequelize
    ".sequelizerc",
    "sequelize.rc",
    # Node / TypeORM
    "ormconfig.json",
    "ormconfig.js",
    "ormconfig.ts",
    "ormconfig.yaml",
    "ormconfig.yml",
    # Node / Prisma
    "schema.prisma",
    # Ruby / Rails
    "database.yml",
    # PHP / Laravel
    "database.php",
    # Java / Hibernate
    "hibernate.cfg.xml",
    "persistence.xml",
    # General
    "db.json",  # Often used for json-server or simple key-value stores
}

# Directories that strongly imply database usage
DB_DIRECTORIES = {
    "migrations",
    "migration",
    "seeds",
    "seeders",
    "fixtures",  # Often contains DB data
}
