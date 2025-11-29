import pytest
import logging
import tempfile
import os
from unittest.mock import patch, MagicMock
from utils.logger import setup_logger, log_performance, performance_logger, log_api_call, log_database_operation, setup_request_logging


class TestLogger:
    def test_setup_logger(self):
        logger = setup_logger("test_logger")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"
        assert logger.level == logging.INFO

        # Check if handlers are set up
        assert len(logger.handlers) == 2  # console and file handlers

    def test_setup_logger_debug_level(self):
        with patch('utils.logger.LOG_LEVEL', 'DEBUG'):
            logger = setup_logger("test_logger")
            assert logger.level == logging.DEBUG

    def test_log_performance_with_records(self):
        with patch('utils.logger.logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            log_performance("test_func", 2.5, 100)

            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert "test_func" in call_args
            assert "2.50s" in call_args
            assert "100" in call_args
            assert "40.00 rec/s" in call_args

    def test_log_performance_without_records(self):
        with patch('utils.logger.logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            log_performance("test_func", 1.5)

            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert "test_func" in call_args
            assert "1.50s" in call_args

    def test_performance_logger_decorator(self):
        with patch('utils.logger.logging.getLogger') as mock_get_logger, \
             patch('utils.logger.log_performance') as mock_log_performance, \
             patch('time.time', side_effect=[0, 1.5]):

            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            @performance_logger
            def test_function():
                return "result"

            result = test_function()

            assert result == "result"
            mock_logger.debug.assert_any_call("Starting test_function")
            mock_logger.debug.assert_any_call("Completed test_function")
            mock_log_performance.assert_called_once_with("test_function", 1.5)

    def test_performance_logger_decorator_with_exception(self):
        with patch('utils.logger.logging.getLogger') as mock_get_logger, \
             patch('time.time', side_effect=[0, 1.0]):

            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            @performance_logger
            def failing_function():
                raise ValueError("Test error")

            with pytest.raises(ValueError, match="Test error"):
                failing_function()

            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args[0][0]
            assert "Error in failing_function" in call_args
            assert "1.00s" in call_args

    def test_log_api_call_success(self):
        with patch('utils.logger.logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            log_api_call("test/endpoint", success=True, duration=1.2)

            mock_logger.debug.assert_called_once_with("API call successful: test/endpoint (1.20s)")

    def test_log_api_call_success_no_duration(self):
        with patch('utils.logger.logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            log_api_call("test/endpoint", success=True)

            mock_logger.debug.assert_called_once_with("API call successful: test/endpoint")

    def test_log_api_call_failure(self):
        with patch('utils.logger.logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            log_api_call("test/endpoint", success=False, params={"key": "value"})

            mock_logger.warning.assert_called_once_with("API call failed: test/endpoint")
            mock_logger.debug.assert_called_once_with("Parameters: {'key': 'value'}")

    def test_log_database_operation_success(self):
        with patch('utils.logger.logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            log_database_operation("INSERT", "stocks", records=10, success=True)

            mock_logger.debug.assert_called_once_with("DB operation successful: INSERT on stocks (10 records)")

    def test_log_database_operation_success_no_records(self):
        with patch('utils.logger.logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            log_database_operation("SELECT", "stocks", success=True)

            mock_logger.debug.assert_called_once_with("DB operation successful: SELECT on stocks")

    def test_log_database_operation_failure(self):
        with patch('utils.logger.logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            log_database_operation("INSERT", "stocks", success=False)

            mock_logger.error.assert_called_once_with("DB operation failed: INSERT on stocks")

    def test_setup_request_logging(self):
        with patch('utils.logger.logging.getLogger') as mock_get_logger:
            mock_urllib_logger = MagicMock()
            mock_requests_logger = MagicMock()
            mock_get_logger.side_effect = lambda name: {
                'urllib3': mock_urllib_logger,
                'requests': mock_requests_logger
            }.get(name, MagicMock())

            setup_request_logging()

            mock_urllib_logger.setLevel.assert_called_once_with(logging.WARNING)
            mock_requests_logger.setLevel.assert_called_once_with(logging.WARNING)
