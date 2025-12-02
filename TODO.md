# Test Coverage Improvement Plan

## Current Status
- Running pytest coverage analysis to determine current coverage percentage
- Existing test files: test_main.py, test_data_modules.py, test_online_data.py

## Information Gathered
- **Main Module (main.py)**: TSEDataCollector class with methods including create_database, load_initial_data, rebuild_table, collect_stocks, collect_sectors, collect_indices, update_price_history, update_ri_history, run_full_update, run_continuous_update
- **API Modules**: 
  - Gravity_tse.py: get_stock_list, get_sector_list, get_index_list, get_price_history, get_price_history_by_date, get_60d_price_history, get_market_watch, get_shareholders, get_instrument_info
  - price_history.py, market_watch.py, tse_api.py, shareholders.py
- **Database Modules**: sqlite_db.py, postgres_db.py
- **Utils**: logger.py, helpers.py
- Current tests cover some main class methods but miss several key functions and entire API/database/utils modules

## Plan
1. **Add tests for untested TSEDataCollector methods**:
   - [x] create_database
   - [x] load_initial_data
   - [x] rebuild_table

2. **Create comprehensive test file for Gravity_tse.py**:
   - Tests for all major functions with proper mocking
   - Edge cases and error handling

3. **Create test file for other API modules**:
   - price_history.py, market_watch.py, tse_api.py, shareholders.py
   - Mock external dependencies

4. **Create test file for database modules**:
   - SQLite and PostgreSQL database operations
   - CRUD operations, error handling

5. **Create test file for utils**:
   - Logger setup and functions
   - Helper functions

6. **Add more edge case tests** for existing functions

## Dependent Files to be edited
- tests/test_main.py: Add tests for untested methods
- tests/test_gravity_tse.py: New file for Gravity_tse API tests
- tests/test_api_modules.py: New file for other API module tests  
- tests/test_database.py: New file for database tests
- tests/test_utils.py: New file for utils tests

## Followup Steps
- Run coverage analysis again after adding tests
- Add more tests if 60% coverage not reached
- Ensure all new tests use mocking to avoid real API calls
- Verify tests run successfully

## Expected Outcome
Increase test coverage from current level to at least 60% by adding comprehensive tests for untested code paths.
