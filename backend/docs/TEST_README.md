# Git Service Tests

This directory contains unit tests for the git service functionality, specifically focusing on the `insert_tree_entry` method.

## Test Files

- `test_git_service.py` - Main test file with comprehensive test cases
- `conftest.py` - Pytest configuration for database setup

## Database Configuration

The tests use the same database configuration as the main application:

- **Uses `DATABASE_URL` environment variable** if available
- **Falls back to `TORTOISE_ORM` configuration** from `database.py`
- **Same database as main application** - no separate test database needed

## Running Tests

### Simple pytest execution

```bash
cd backend
python -m pytest test_git_service.py -v
```

The tests will automatically use the same database configuration as your main application.

### Environment Variables

The tests will use these environment variables if available:
- `DATABASE_URL` - Full database connection string
- `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME` - Individual database parameters

## Test Coverage

The tests cover the following scenarios for `insert_tree_entry`:

### Basic Functionality
- ✅ Inserting entries at root level
- ✅ Inserting entries in nested directories
- ✅ Inserting entries in deeply nested paths (3+ levels)
- ✅ Inserting directory entries (tree type)

### Edge Cases
- ✅ Preserving existing entries when adding new ones
- ✅ Multiple entries at the same path level
- ✅ Error handling for invalid paths

### Supporting Functions
- ✅ `resolve_tree` function with empty paths
- ✅ `resolve_tree` function with single and multiple level paths
- ✅ Error handling for invalid paths in `resolve_tree`

## Test Structure

```
TestIndexInsertTreeEntry/
├── test_insert_tree_entry_simple_path
├── test_insert_tree_entry_nested_path
├── test_insert_tree_entry_deep_nested_path
├── test_insert_tree_entry_with_tree_type
├── test_insert_tree_entry_preserves_existing_entries
├── test_insert_tree_entry_invalid_path_raises_error
└── test_insert_tree_entry_multiple_entries_same_path

TestResolveTree/
├── test_resolve_tree_empty_path
├── test_resolve_tree_single_level
├── test_resolve_tree_multiple_levels
└── test_resolve_tree_invalid_path_raises_error
```

## Dependencies

The tests require the following additional dependencies (already added to `requirements.txt`):
- `pytest`
- `pytest-asyncio`

## Database Setup

The tests use Tortoise ORM's test utilities to:
1. Initialize the database connection
2. Generate schemas automatically
3. Clean up after each test
4. Use the same models as the main application

## Running Specific Tests

To run a specific test:

```bash
# Run a specific test method
python -m pytest test_git_service.py::TestIndexInsertTreeEntry::test_insert_tree_entry_simple_path -v

# Run all tests in a specific class
python -m pytest test_git_service.py::TestIndexInsertTreeEntry -v

# Run tests with specific markers
python -m pytest test_git_service.py -m "asyncio" -v
```

## Troubleshooting

### Database Connection Issues
- Ensure PostgreSQL is running
- Check that the database credentials are correct
- Verify that the database exists

### Import Errors
- Make sure you're running tests from the `backend` directory
- Ensure all dependencies are installed: `pip install -r requirements.txt`

### Test Failures
- Check that the database schema is up to date
- Verify that the git service code hasn't changed significantly
- Look at the test output for specific error messages 