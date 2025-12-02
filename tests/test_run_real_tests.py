"""
Tests for run_real_tests.py script
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os
from pathlib import Path
import run_real_tests


class TestRunRealTests:
    """Test run_real_tests script functions"""

    @patch('run_real_tests.subprocess.run')
    @patch('run_real_tests.Path')
    @patch('run_real_tests.os.chdir')
    def test_run_real_tests_success(self, mock_chdir, mock_path, mock_subprocess_run):
        """Test successful run of real tests"""
        # Mock Path
        mock_path_instance = MagicMock()
        mock_path_instance.parent = Path('/fake/path')
        mock_path.return_value = mock_path_instance

        # Mock subprocess.run to succeed
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_subprocess_run.return_value = mock_result

        result = run_real_tests.run_real_tests()

        assert result == 0
        assert mock_subprocess_run.call_count == 1
        mock_chdir.assert_called_once_with(Path('/fake/path'))

    @patch('run_real_tests.subprocess.run')
    @patch('run_real_tests.Path')
    @patch('run_real_tests.os.chdir')
    def test_run_real_tests_failure(self, mock_chdir, mock_path, mock_subprocess_run):
        """Test failed run of real tests"""
        # Mock Path
        mock_path_instance = MagicMock()
        mock_path_instance.parent = Path('/fake/path')
        mock_path.return_value = mock_path_instance

        # Mock subprocess.run to fail
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_subprocess_run.return_value = mock_result

        result = run_real_tests.run_real_tests()

        assert result == 1

    @patch('run_real_tests.subprocess.run')
    @patch('run_real_tests.Path')
    @patch('run_real_tests.os.chdir')
    def test_run_real_tests_timeout(self, mock_chdir, mock_path, mock_subprocess_run):
        """Test timeout in real tests"""
        # Mock Path
        mock_path_instance = MagicMock()
        mock_path_instance.parent = Path('/fake/path')
        mock_path.return_value = mock_path_instance

        # Mock subprocess.run to raise TimeoutExpired
        mock_subprocess_run.side_effect = run_real_tests.subprocess.TimeoutExpired(cmd=['pytest'], timeout=3600)

        result = run_real_tests.run_real_tests()

        assert result == 1

    @patch('builtins.print')
    def test_show_test_info(self, mock_print):
        """Test showing test info"""
        run_real_tests.show_test_info()

        # Check that print was called multiple times
        assert mock_print.call_count > 10

    @patch('run_real_tests.show_test_info')
    @patch('run_real_tests.run_real_tests')
    def test_main_help(self, mock_run_tests, mock_show_info):
        """Test main with help argument"""
        with patch('sys.argv', ['run_real_tests.py', '--help']):
            result = run_real_tests.main()

        assert result == 0
        mock_show_info.assert_called_once()
        mock_run_tests.assert_not_called()

    @patch('run_real_tests.show_test_info')
    @patch('run_real_tests.run_real_tests')
    def test_main_info(self, mock_run_tests, mock_show_info):
        """Test main with info argument"""
        with patch('sys.argv', ['run_real_tests.py', '--info']):
            result = run_real_tests.main()

        assert result == 0
        mock_show_info.assert_called_once()
        mock_run_tests.assert_not_called()

    @patch('run_real_tests.run_real_tests')
    def test_main_default(self, mock_run_tests):
        """Test main with no arguments"""
        mock_run_tests.return_value = 0
        with patch('sys.argv', ['run_real_tests.py']):
            result = run_real_tests.main()

        assert result == 0
        mock_run_tests.assert_called_once()