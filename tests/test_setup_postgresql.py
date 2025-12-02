"""
Tests for setup_postgresql.py script
"""

import pytest
from unittest.mock import patch, MagicMock, mock_open
import sys
import platform
import shutil
from pathlib import Path
import setup_postgresql


class TestPostgreSQLConfig:
    """Test PostgreSQLConfig dataclass"""

    def test_default_config(self):
        """Test default configuration values"""
        config = setup_postgresql.PostgreSQLConfig()
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.user == "postgres"
        assert config.password == "password"
        assert config.database == "tse_db"
        assert config.install_deps == True
        assert config.create_db == True
        assert config.create_env_file == True
        assert config.create_config_file == True


class TestProfessionalPostgreSQLSetup:
    """Test ProfessionalPostgreSQLSetup class"""

    def setup_method(self):
        """Setup test instance"""
        self.config = setup_postgresql.PostgreSQLConfig()
        self.setup = setup_postgresql.ProfessionalPostgreSQLSetup(self.config)

    @patch('setup_postgresql.subprocess.run')
    def test_check_postgresql_installed_success(self, mock_run):
        """Test successful PostgreSQL installation check"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "psql (PostgreSQL) 15.3"
        mock_run.return_value = mock_result

        result = self.setup.check_postgresql_installed()

        assert result == True
        mock_run.assert_called_once_with(
            ['psql', '--version'],
            capture_output=True,
            text=True,
            timeout=10
        )

    @patch('setup_postgresql.subprocess.run')
    def test_check_postgresql_installed_failure(self, mock_run):
        """Test failed PostgreSQL installation check"""
        mock_run.side_effect = FileNotFoundError()

        result = self.setup.check_postgresql_installed()

        assert result == False

    @patch('setup_postgresql.shutil.which')
    @patch('setup_postgresql.subprocess.run')
    def test_install_postgresql_linux_apt(self, mock_run, mock_which):
        """Test PostgreSQL installation on Linux with apt"""
        mock_which.return_value = True  # apt available
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        with patch.object(self.setup, '_log'):
            result = self.setup.install_postgresql_linux()

        assert result == True
        assert mock_run.call_count == 2  # apt update and install

    @patch('setup_postgresql.shutil.which')
    def test_install_postgresql_linux_no_package_manager(self, mock_which):
        """Test PostgreSQL installation failure on Linux without package manager"""
        mock_which.return_value = None

        result = self.setup.install_postgresql_linux()

        assert result == False

    @patch('setup_postgresql.shutil.which')
    @patch('setup_postgresql.subprocess.run')
    def test_install_postgresql_macos_success(self, mock_run, mock_which):
        """Test successful PostgreSQL installation on macOS"""
        mock_which.return_value = True  # brew available
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        with patch.object(self.setup, '_log'):
            result = self.setup.install_postgresql_macos()

        assert result == True

    @patch('setup_postgresql.shutil.which')
    def test_install_postgresql_macos_no_brew(self, mock_which):
        """Test PostgreSQL installation failure on macOS without brew"""
        mock_which.return_value = None

        result = self.setup.install_postgresql_macos()

        assert result == False

    def test_install_postgresql_windows(self):
        """Test PostgreSQL installation on Windows"""
        result = self.setup.install_postgresql_windows()

        assert result == False  # Manual installation required

    @patch('setup_postgresql.platform.system')
    def test_install_postgresql_unsupported_platform(self, mock_system):
        """Test PostgreSQL installation on unsupported platform"""
        mock_system.return_value = "unknown"

        result = self.setup.install_postgresql()

        assert result == False

    @patch('setup_postgresql.sys.executable')
    @patch('setup_postgresql.subprocess.run')
    def test_install_python_dependencies_success(self, mock_run, mock_executable):
        """Test successful Python dependencies installation"""
        mock_executable.__str__ = lambda x: 'python'
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        with patch.object(self.setup, '_log'):
            result = self.setup.install_python_dependencies()

        assert result == True
        assert mock_run.call_count == 3  # Three packages

    @patch('setup_postgresql.subprocess.run')
    def test_create_database_success(self, mock_run):
        """Test successful database creation"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        with patch.object(self.setup, '_log'):
            result = self.setup.create_database()

        assert result == True

    @patch('setup_postgresql.subprocess.run')
    def test_create_database_already_exists(self, mock_run):
        """Test database creation when database already exists"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "already exists"
        mock_run.return_value = mock_result

        with patch.object(self.setup, '_log'):
            result = self.setup.create_database()

        assert result == True

    @patch('setup_postgresql.Path')
    @patch('builtins.open', new_callable=mock_open)
    def test_create_env_file_success(self, mock_file, mock_path):
        """Test successful .env file creation"""
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance

        result = self.setup.create_env_file()

        assert result == True
        mock_file.assert_called_once()

    @patch('setup_postgresql.Path')
    @patch('builtins.open', new_callable=mock_open)
    def test_create_config_file_success(self, mock_file, mock_path):
        """Test successful config file creation"""
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance

        result = self.setup.create_config_file()

        assert result == True
        mock_file.assert_called_once()

    @patch('setup_postgresql.subprocess.run')
    def test_test_connection_success(self, mock_run):
        """Test successful connection test"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = self.setup.test_connection()

        assert result == True

    @patch('setup_postgresql.subprocess.run')
    def test_test_connection_failure(self, mock_run):
        """Test failed connection test"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "connection failed"
        mock_run.return_value = mock_result

        result = self.setup.test_connection()

        assert result == False

    @patch('setup_postgresql.ProfessionalPostgreSQLSetup.check_postgresql_installed')
    @patch('setup_postgresql.ProfessionalPostgreSQLSetup.install_postgresql')
    @patch('setup_postgresql.ProfessionalPostgreSQLSetup.install_python_dependencies')
    @patch('setup_postgresql.ProfessionalPostgreSQLSetup.create_database')
    @patch('setup_postgresql.ProfessionalPostgreSQLSetup.create_env_file')
    @patch('setup_postgresql.ProfessionalPostgreSQLSetup.create_config_file')
    @patch('setup_postgresql.ProfessionalPostgreSQLSetup.test_connection')
    def test_run_setup_success(self, mock_test_conn, mock_create_config, mock_create_env,
                              mock_create_db, mock_install_deps, mock_install_pg, mock_check_pg):
        """Test successful complete setup"""
        mock_check_pg.return_value = True
        mock_install_pg.return_value = True
        mock_install_deps.return_value = True
        mock_create_db.return_value = True
        mock_create_env.return_value = True
        mock_create_config.return_value = True
        mock_test_conn.return_value = True

        result = self.setup.run_setup()

        assert result == True

    @patch('setup_postgresql.ProfessionalPostgreSQLSetup.check_postgresql_installed')
    @patch('setup_postgresql.ProfessionalPostgreSQLSetup.install_postgresql')
    def test_run_setup_failure(self, mock_install_pg, mock_check_pg):
        """Test setup failure"""
        mock_check_pg.return_value = True
        mock_install_pg.return_value = False

        result = self.setup.run_setup()

        assert result == False


class TestMainFunctions:
    """Test main functions"""

    @patch('setup_postgresql.argparse.ArgumentParser.parse_args')
    @patch('setup_postgresql.ProfessionalPostgreSQLSetup.run_setup')
    def test_main_success(self, mock_run_setup, mock_parse_args):
        """Test successful main execution"""
        mock_args = MagicMock()
        mock_parse_args.return_value = mock_args
        mock_run_setup.return_value = True

        with patch('sys.exit') as mock_exit:
            setup_postgresql.main()

        mock_exit.assert_called_once_with(0)

    @patch('setup_postgresql.argparse.ArgumentParser.parse_args')
    @patch('setup_postgresql.ProfessionalPostgreSQLSetup.run_setup')
    def test_main_failure(self, mock_run_setup, mock_parse_args):
        """Test failed main execution"""
        mock_args = MagicMock()
        mock_parse_args.return_value = mock_args
        mock_run_setup.return_value = False

        with patch('sys.exit') as mock_exit:
            setup_postgresql.main()

        mock_exit.assert_called_once_with(1)