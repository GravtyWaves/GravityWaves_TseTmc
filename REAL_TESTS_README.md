# TSE Real Data Integration Tests

Comprehensive test suite with 95% coverage for the TSE Data Collector using real API data.

## Quick Start

### Run All Real Data Tests
```bash
python run_real_tests.py
```

### Alternative: Run with pytest directly
```bash
python -m pytest tests/test_real_data.py -v --tb=short
```

## Test Coverage

This test suite covers approximately 95% of the TSE data collector functionality:

### 🔹 API Connectivity & Data Fetching (15 tests)
- Real stock list retrieval from TSE API
- Real sector and index data collection
- Price history and client type (RI) history fetching
- Instrument search and details
- Intraday trades and shareholder data

### 🔹 Data Processing & Validation (10 tests)
- API response parsing and validation
- Data structure and type checking
- Date range generation and validation
- Sector-stock relationship consistency
- Index data completeness

### 🔹 Database Operations (8 tests)
- Full data collection workflow
- Incremental updates and duplicate handling
- Data integrity and foreign key relationships
- Cross-database compatibility (SQLite/PostgreSQL)
- Connection pooling under load

### 🔹 Performance & Scalability (6 tests)
- Memory usage monitoring during large operations
- Concurrent database operations
- Large dataset handling (1 year of data)
- API rate limiting and throttling
- System resource monitoring

### 🔹 Error Handling & Resilience (7 tests)
- Network failure recovery and retry logic
- Invalid input handling and graceful degradation
- Database connection issues and recovery
- API timeout and error response handling
- Simulated failure scenarios

### 🔹 System Integration (6 tests)
- Configuration management and environment handling
- Logging and audit trail functionality
- Backup and recovery operations
- Security validation and input sanitization
- Maintenance operations and cleanup

## Test Execution Options

### Run Specific Test Categories
```bash
# Run only fast tests (skip slow performance tests)
python -m pytest tests/test_real_data.py -m "not slow" -v

# Run only API connectivity tests
python -m pytest tests/test_real_data.py::TestRealDataIntegration::test_real_stock_list_fetch -v

# Run performance tests only
python -m pytest tests/test_real_data.py -k "performance or memory" -v
```

### Run with Different Output Formats
```bash
# Detailed output with durations
python -m pytest tests/test_real_data.py -v --durations=10

# Generate HTML coverage report
python -m pytest tests/test_real_data.py --cov=. --cov-report=html

# Run with parallel execution (if pytest-xdist installed)
python -m pytest tests/test_real_data.py -n auto
```

## Prerequisites

- **Internet Connection**: Active connection required for TSE API access
- **Python Dependencies**: All packages in `requirements.txt` must be installed
- **Database**: SQLite (included) or PostgreSQL (optional)

## Expected Runtime

- **Full Test Suite**: 30-60 minutes (depending on network speed and API response times)
- **Fast Tests Only**: 10-15 minutes
- **API Connectivity Only**: 2-5 minutes

## Test Results Interpretation

### ✅ PASSED
- All functionality working correctly with real TSE API data
- Data collection, processing, and storage successful
- Error handling and recovery working properly

### ⚠️ WARNINGS
- Some tests may show warnings for deprecated features (expected)
- Network-related warnings may appear during API calls

### ❌ FAILED
- Check specific error messages for issues
- Common causes: network connectivity, API changes, database issues

## Troubleshooting

### Network Issues
```bash
# Test basic connectivity
python -c "import requests; print(requests.get('http://www.tsetmc.com').status_code)"
```

### Database Issues
```bash
# Reset test database
rm -f test_*.db
```

### API Changes
If tests fail due to API changes, check:
1. TSE API endpoint availability
2. Response format changes
3. Rate limiting policies

## Configuration

Tests use temporary SQLite databases by default. To test with PostgreSQL:

1. Set up PostgreSQL database
2. Update `config.py` with PostgreSQL connection details
3. Modify test fixtures to use PostgreSQL instead of SQLite

## Contributing

When adding new tests:
1. Follow the existing naming convention: `test_real_*`
2. Add appropriate pytest markers (`@pytest.mark.slow` for performance tests)
3. Include docstrings explaining what the test covers
4. Ensure tests are idempotent and don't interfere with each other

## Support

For issues with real data tests:
1. Verify internet connectivity to TSE API
2. Check TSE website availability
3. Review error messages for specific failure reasons
4. Consider running tests during Tehran business hours for best results
