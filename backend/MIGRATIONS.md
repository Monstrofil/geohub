# Database Migrations with Aerich

This project uses [Aerich](https://github.com/tortoise/aerich) for database migrations with Tortoise ORM.

## Setup

### 1. Initialize Aerich (First time only)
```bash
cd backend
aerich init -t database.TORTOISE_ORM
```

This creates the initial migration configuration.

### 2. Initialize Database
```bash
aerich init-db
```

This creates the initial migration and sets up the database schema.

### 3. Create a Migration
When you make changes to models, create a migration:
```bash
aerich migrate --name "add_base_file_type_field"
```

### 4. Apply Migrations
Apply pending migrations to update the database:
```bash
aerich upgrade
```

## Available Commands

| Command | Description |
|---------|-------------|
| `aerich init -t database.TORTOISE_ORM` | Initialize Aerich configuration |
| `aerich init-db` | Initialize database with initial migration |
| `aerich migrate --name <name>` | Create a new migration |
| `aerich migrate --name <name> --empty` | Create empty migration for manual editing |
| `aerich upgrade` | Apply pending migrations |
| `aerich downgrade` | Rollback last migration |
| `aerich history` | Show migration history |
| `aerich heads` | Show current migration heads |

## Migration Workflow

### For New Features
1. Update your models in `models.py`
2. Create a migration: `aerich migrate --name "Description of changes"`
3. Apply the migration: `aerich upgrade`

### For Data Migration
If you need to migrate existing data (like adding base_file_type to existing files), create a custom migration:
```bash
aerich migrate --name "migrate_existing_data" --empty
```

Then edit the generated migration file to add your data migration logic.

## Migration Files

Migrations are stored in the `migrations/` directory:
- `migrations/` - Contains all migration files
- `pyproject.toml` - Aerich configuration (created by `aerich init`)

## Troubleshooting

### Reset Migrations
If you need to start fresh:
1. Delete the `migrations/` directory
2. Run `aerich init -t database.TORTOISE_ORM`
3. Run `aerich init-db`

### Check Migration Status
```bash
aerich history
```

### Rollback Last Migration
```bash
aerich downgrade
```

## Example Workflow

```bash
# 1. Initialize (first time)
aerich init -t database.TORTOISE_ORM
aerich init-db

# 2. Make changes to models.py
# (add new fields, change field types, etc.)

# 3. Create migration
aerich migrate --name "add_user_preferences_field"

# 4. Apply migration
aerich upgrade

# 5. If you need custom data migration
aerich migrate --name "migrate_existing_data" --empty
# Then edit the generated migration file
```

## Notes

- Always backup your database before running migrations in production
- Test migrations on a copy of your production data first
- Use `--empty` flag for custom data migrations
- Aerich automatically detects column renames and asks for confirmation 