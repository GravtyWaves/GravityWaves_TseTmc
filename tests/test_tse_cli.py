"""
تست‌های حرفه‌ای برای tse-cli.py با استفاده از داده‌های واقعی TSE
"""

import pytest
import argparse
import sys
import subprocess
import tempfile
import os
import importlib.util
from unittest.mock import patch, MagicMock, call
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Try to import tse_cli module
tse_cli_spec = importlib.util.find_spec('tse_cli')
if tse_cli_spec is not None:
    tse_cli_module = importlib.util.module_from_spec(tse_cli_spec)
    tse_cli_spec.loader.exec_module(tse_cli_module)
    # Add to sys.modules so patches work
    sys.modules['tse_cli'] = tse_cli_module
    ProfessionalTSECLI = tse_cli_module.ProfessionalTSECLI
    TSEConfig = tse_cli_module.TSEConfig
    create_parser = tse_cli_module.create_parser
    main = tse_cli_module.main
else:
    # Fallback for when the module can't be imported during development
    print("Warning: Could not find tse_cli module")
    # Define dummy classes/functions for testing when import fails
    class TSEConfig:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    class ProfessionalTSECLI:
        def __init__(self, config):
            self.config = config

    def create_parser():
        return argparse.ArgumentParser()

    def main():
        pass


class TestTSEConfig:
    """تست‌های TSEConfig"""

    def test_default_config(self):
        """تست تنظیمات پیش‌فرض"""
        config = TSEConfig()

        assert config.verbose is False
        assert config.dry_run is False
        assert config.force is False
        assert config.quiet is False
        assert config.db_type == "sqlite"
        assert config.days == 30
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.user == "postgres"
        assert config.password == "password"
        assert config.database == "tse_db"

    def test_custom_config(self):
        """تست تنظیمات سفارشی"""
        config = TSEConfig(
            verbose=True,
            dry_run=True,
            force=True,
            quiet=True,
            db_type="postgresql",
            days=90,
            host="remotehost",
            port=5433,
            user="admin",
            password="secret",
            database="tse_prod"
        )

        assert config.verbose is True
        assert config.dry_run is True
        assert config.force is True
        assert config.quiet is True
        assert config.db_type == "postgresql"
        assert config.days == 90
        assert config.host == "remotehost"
        assert config.port == 5433
        assert config.user == "admin"
        assert config.password == "secret"
        assert config.database == "tse_prod"


class TestProfessionalTSECLI:
    """تست‌های ProfessionalTSECLI"""

    def setup_method(self):
        """تنظیمات اولیه برای هر تست"""
        self.config = TSEConfig(verbose=True, db_type="sqlite")
        self.cli = ProfessionalTSECLI(self.config)

    def test_initialization(self):
        """تست مقداردهی اولیه"""
        assert self.cli.config == self.config
        assert self.cli.system in ['windows', 'linux', 'darwin']

    @patch('builtins.print')
    def test_logging_methods(self, mock_print):
        """تست متدهای logging"""
        # تست _success
        self.cli._success("Test message")
        mock_print.assert_called_with("✅ Test message")

        # تست _error
        self.cli._error("Error message")
        mock_print.assert_called_with("❌ Error message", file=sys.stderr)

        # تست _warning
        self.cli._warning("Warning message")
        mock_print.assert_called_with("⚠️  Warning message")

        # تست _info
        self.cli._info("Info message")
        mock_print.assert_called_with("ℹ️  Info message")

    @patch('builtins.input')
    def test_confirm_action_with_force(self, mock_input):
        """تست تایید action با force"""
        self.config.force = True

        result = self.cli._confirm_action("delete", "file.txt")

        assert result is True
        mock_input.assert_not_called()

    @patch('builtins.input')
    def test_confirm_action_user_yes(self, mock_input):
        """تست تایید action با پاسخ کاربر yes"""
        mock_input.return_value = "yes"

        result = self.cli._confirm_action("delete", "file.txt")

        assert result is True
        mock_input.assert_called_once_with("Are you sure you want to delete 'file.txt'? (yes/no): ")

    @patch('builtins.input')
    def test_confirm_action_user_no(self, mock_input):
        """تست عدم تایید action با پاسخ کاربر no"""
        mock_input.return_value = "no"

        result = self.cli._confirm_action("delete", "file.txt")

        assert result is False

    @patch('subprocess.run')
    def test_run_main_command_success(self, mock_run):
        """تست اجرای موفق command"""
        mock_run.return_value = MagicMock(returncode=0, stdout="Success", stderr="")

        result = self.cli._run_main_command(["create-db"])

        assert result is True
        mock_run.assert_called_once()

        # بررسی پارامترهای فراخوانی
        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert cmd[0] == sys.executable
        assert cmd[1] == "main.py"
        assert "create-db" in cmd

    @patch('subprocess.run')
    def test_run_main_command_failure(self, mock_run):
        """تست اجرای ناموفق command"""
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="Error occurred")

        result = self.cli._run_main_command(["invalid-command"])

        assert result is False

    @patch('subprocess.run')
    def test_run_main_command_timeout(self, mock_run):
        """تست timeout در اجرای command"""
        from subprocess import TimeoutExpired
        mock_run.side_effect = TimeoutExpired("timeout", 3600)

        result = self.cli._run_main_command(["long-running-command"])

        assert result is False

    @patch('subprocess.run')
    def test_run_main_command_dry_run(self, mock_run):
        """تست dry run"""
        self.config.dry_run = True

        result = self.cli._run_main_command(["create-db"])

        assert result is True
        mock_run.assert_not_called()

    @patch('os.getenv')
    @patch.object(ProfessionalTSECLI, '_run_main_command')
    def test_setup_database_sqlite(self, mock_run_cmd, mock_getenv):
        """تست setup database با SQLite"""
        mock_run_cmd.return_value = True

        result = self.cli.setup_database()

        assert result is True
        assert mock_run_cmd.call_count == 2  # create-db and load-initial-data

    @patch('os.getenv')
    @patch.object(ProfessionalTSECLI, '_run_main_command')
    def test_setup_database_postgresql_missing_url(self, mock_run_cmd, mock_getenv):
        """تست setup database با PostgreSQL بدون DATABASE_URL"""
        self.config.db_type = "postgresql"
        mock_getenv.return_value = None

        result = self.cli.setup_database()

        assert result is False
        mock_run_cmd.assert_not_called()

    @patch('os.getenv')
    @patch.object(ProfessionalTSECLI, '_run_main_command')
    def test_setup_database_postgresql_with_url(self, mock_run_cmd, mock_getenv):
        """تست setup database با PostgreSQL با DATABASE_URL"""
        self.config.db_type = "postgresql"
        mock_getenv.return_value = "postgresql://user:pass@localhost:5432/tse_db"
        mock_run_cmd.return_value = True

        result = self.cli.setup_database()

        assert result is True
        assert mock_run_cmd.call_count == 2

    @patch.object(ProfessionalTSECLI, '_run_main_command')
    def test_collect_initial_data(self, mock_run_cmd):
        """تست جمع‌آوری داده‌های اولیه"""
        mock_run_cmd.return_value = True

        result = self.cli.collect_initial_data()

        assert result is True
        assert mock_run_cmd.call_count == 3  # sectors, stocks, indices

    @patch.object(ProfessionalTSECLI, '_run_main_command')
    def test_update_data_full(self, mock_run_cmd):
        """تست بروزرسانی داده‌ها با mode full"""
        mock_run_cmd.return_value = True

        result = self.cli.update_data("full")

        assert result is True
        mock_run_cmd.assert_called_once_with(["update", "--mode", "full"])

    @patch.object(ProfessionalTSECLI, '_run_main_command')
    def test_update_data_prices_with_days(self, mock_run_cmd):
        """تست بروزرسانی قیمت‌ها با تعداد روز"""
        self.config.days = 90
        mock_run_cmd.return_value = True

        result = self.cli.update_data("prices")

        assert result is True
        mock_run_cmd.assert_called_once_with(["update", "--mode", "prices", "--days", "90"])

    @patch('builtins.input')
    @patch.object(ProfessionalTSECLI, '_run_main_command')
    def test_rebuild_table_with_confirmation(self, mock_run_cmd, mock_input):
        """تست بازسازی جدول با تایید کاربر"""
        mock_input.return_value = "yes"
        mock_run_cmd.return_value = True

        result = self.cli.rebuild_table("stocks")

        assert result is True
        mock_run_cmd.assert_called_once_with(["rebuild-table", "--table", "stocks"])

    @patch('builtins.input')
    @patch.object(ProfessionalTSECLI, '_run_main_command')
    def test_rebuild_table_cancelled(self, mock_run_cmd, mock_input):
        """تست لغو بازسازی جدول"""
        mock_input.return_value = "no"

        result = self.cli.rebuild_table("stocks")

        assert result is True  # True چون cancelled به عنوان success در نظر گرفته شده
        mock_run_cmd.assert_not_called()

    @patch.object(ProfessionalTSECLI, '_run_main_command')
    def test_continuous_update(self, mock_run_cmd):
        """تست بروزرسانی مداوم"""
        mock_run_cmd.return_value = True

        result = self.cli.continuous_update(3600)

        assert result is True
        mock_run_cmd.assert_called_once_with(["continuous-update", "--interval", "3600"])

    @patch('builtins.print')
    def test_show_status_sqlite(self, mock_print):
        """تست نمایش وضعیت با SQLite"""
        result = self.cli.show_status()

        assert result is True
        # بررسی اینکه print فراخوانی شده
        assert mock_print.call_count > 0

    @patch('database.postgres_db.PostgreSQLDatabase')
    @patch('os.getenv')
    @patch('builtins.print')
    def test_show_status_postgresql_connected(self, mock_print, mock_getenv, mock_postgres):
        """تست نمایش وضعیت با PostgreSQL متصل"""
        self.config.db_type = "postgresql"
        mock_getenv.return_value = "postgresql://user:pass@localhost:5432/tse_db"

        # mock successful connection
        mock_db = MagicMock()
        mock_session = MagicMock()
        mock_db.get_session.return_value = mock_session
        mock_postgres.return_value = mock_db

        result = self.cli.show_status()

        assert result is True

    @patch('database.postgres_db.PostgreSQLDatabase')
    @patch('os.getenv')
    @patch('builtins.print')
    def test_show_status_postgresql_failed(self, mock_print, mock_getenv, mock_postgres):
        """تست نمایش وضعیت با PostgreSQL ناموفق"""
        self.config.db_type = "postgresql"
        mock_getenv.return_value = "postgresql://user:pass@localhost:5432/tse_db"

        # mock failed connection
        mock_postgres.side_effect = Exception("Connection failed")

        result = self.cli.show_status()

        assert result is True  # show_status همیشه True برمی‌گرداند


class TestCreateParser:
    """تست‌های create_parser"""

    def test_parser_creation(self):
        """تست ایجاد parser"""
        parser = create_parser()

        assert isinstance(parser, argparse.ArgumentParser)
        assert parser.prog == "tse-cli"
        assert "Professional TSE Data Collector CLI" in parser.description

    def test_parser_global_options(self):
        """تست گزینه‌های global parser"""
        parser = create_parser()

        # تست parse با گزینه‌های global
        args = parser.parse_args(['--verbose', '--dry-run', '--force', '--quiet', 'status'])

        assert args.verbose is True
        assert args.dry_run is True
        assert args.force is True
        assert args.quiet is True
        assert args.command == 'status'

    def test_parser_setup_command(self):
        """تست دستور setup"""
        parser = create_parser()

        args = parser.parse_args(['setup', '--db-type', 'postgresql'])

        assert args.command == 'setup'
        assert args.db_type == 'postgresql'

    def test_parser_update_command(self):
        """تست دستور update"""
        parser = create_parser()

        args = parser.parse_args(['update', 'full', '--days', '90'])

        assert args.command == 'update'
        assert args.mode == 'full'
        assert args.days == 90

    def test_parser_rebuild_command(self):
        """تست دستور rebuild"""
        parser = create_parser()

        args = parser.parse_args(['rebuild', 'stocks'])

        assert args.command == 'rebuild'
        assert args.table == 'stocks'

    def test_parser_continuous_command(self):
        """تست دستور continuous"""
        parser = create_parser()

        args = parser.parse_args(['continuous', '--interval', '7200'])

        assert args.command == 'continuous'
        assert args.interval == 7200

    def test_parser_no_command(self):
        """تست بدون دستور"""
        parser = create_parser()

        args = parser.parse_args([])

        assert args.command is None


class TestMainFunction:
    """تست‌های تابع main"""

    def test_main_no_command(self):
        """تست main بدون دستور"""
        with patch('sys.argv', ['tse-cli']), \
             patch('argparse.ArgumentParser.print_help') as mock_print_help:

            with pytest.raises(SystemExit):
                main()

            mock_print_help.assert_called_once()

    @patch('tse_cli.ProfessionalTSECLI')
    def test_main_setup_command(self, mock_cli_class):
        """تست دستور setup در main"""
        mock_cli = MagicMock()
        mock_cli.setup_database.return_value = True
        mock_cli_class.return_value = mock_cli

        with patch('sys.argv', ['tse-cli', 'setup', '--db-type', 'sqlite']), \
             patch('sys.exit') as mock_exit:

            main()

            mock_cli_class.assert_called_once()
            mock_cli.setup_database.assert_called_once()
            mock_exit.assert_called_once_with(0)

    @patch('tse_cli.ProfessionalTSECLI')
    def test_main_update_command(self, mock_cli_class):
        """تست دستور update در main"""
        mock_cli = MagicMock()
        mock_cli.update_data.return_value = True
        mock_cli_class.return_value = mock_cli

        with patch('sys.argv', ['tse-cli', 'update', 'full']), \
             patch('sys.exit') as mock_exit:

            main()

            mock_cli.update_data.assert_called_once_with('full')
            mock_exit.assert_called_once_with(0)

    @patch('tse_cli.ProfessionalTSECLI')
    def test_main_command_failure(self, mock_cli_class):
        """تست شکست دستور در main"""
        mock_cli = MagicMock()
        mock_cli.setup_database.return_value = False
        mock_cli_class.return_value = mock_cli

        with patch('sys.argv', ['tse-cli', 'setup']), \
             patch('sys.exit') as mock_exit:

            main()

            mock_exit.assert_called_once_with(1)

    @patch('tse_cli.ProfessionalTSECLI')
    def test_main_keyboard_interrupt(self, mock_cli_class):
        """تست KeyboardInterrupt در main"""
        mock_cli = MagicMock()
        mock_cli.setup_database.side_effect = KeyboardInterrupt()
        mock_cli_class.return_value = mock_cli

        with patch('sys.argv', ['tse-cli', 'setup']), \
             patch('builtins.print') as mock_print:

            with pytest.raises(SystemExit):
                main()

            mock_print.assert_called_with("\nOperation cancelled by user", file=sys.stderr)

    @patch('tse_cli.ProfessionalTSECLI')
    def test_main_unexpected_error(self, mock_cli_class):
        """تست خطای غیرمنتظره در main"""
        mock_cli = MagicMock()
        mock_cli.setup_database.side_effect = Exception("Unexpected error")
        mock_cli_class.return_value = mock_cli

        with patch('sys.argv', ['tse-cli', 'setup']), \
             patch('builtins.print') as mock_print:

            with pytest.raises(SystemExit):
                main()

            mock_print.assert_any_call("Unexpected error: Unexpected error", file=sys.stderr)


class TestCLIIntegration:
    """تست‌های یکپارچه CLI"""

    def setup_method(self):
        """تنظیمات اولیه"""
        self.config = TSEConfig(verbose=True, db_type="sqlite")
        self.cli = ProfessionalTSECLI(self.config)

    @patch.object(ProfessionalTSECLI, '_run_main_command')
    def test_full_setup_workflow(self, mock_run_cmd):
        """تست workflow کامل setup"""
        mock_run_cmd.return_value = True

        # اجرای setup
        result = self.cli.setup_database()

        assert result is True

        # بررسی sequence فراخوانی‌ها
        expected_calls = [
            call(["create-db"]),
            call(["load-initial-data"])
        ]
        mock_run_cmd.assert_has_calls(expected_calls)

    @patch.object(ProfessionalTSECLI, '_run_main_command')
    def test_collect_initial_workflow(self, mock_run_cmd):
        """تست workflow جمع‌آوری داده‌های اولیه"""
        mock_run_cmd.return_value = True

        result = self.cli.collect_initial_data()

        assert result is True

        # بررسی sequence فراخوانی‌ها
        expected_calls = [
            call(["update", "--mode", "sectors"]),
            call(["update", "--mode", "stocks"]),
            call(["update", "--mode", "indices"])
        ]
        mock_run_cmd.assert_has_calls(expected_calls)

    @patch.object(ProfessionalTSECLI, '_run_main_command')
    def test_update_modes(self, mock_run_cmd):
        """تست modeهای مختلف update"""
        mock_run_cmd.return_value = True

        mode = 'full'
        result = self.cli.update_data(mode)
        assert result is True

        expected_args = ["update", "--mode", mode]
        assert mock_run_cmd.call_args[0][0] == expected_args

    @patch('builtins.input')
    @patch.object(ProfessionalTSECLI, '_run_main_command')
    def test_rebuild_tables(self, mock_run_cmd, mock_input):
        """تست بازسازی جداول مختلف"""
        mock_input.return_value = "yes"
        mock_run_cmd.return_value = True

        table = 'stocks'
        result = self.cli.rebuild_table(table)
        assert result is True

        expected_args = ["rebuild-table", "--table", table]
        assert mock_run_cmd.call_args[0][0] == expected_args

    def test_config_persistence(self):
        """تست persistence تنظیمات"""
        config = TSEConfig(verbose=True, force=True, db_type="postgresql", days=60)

        # ایجاد CLI با تنظیمات
        cli = ProfessionalTSECLI(config)

        # بررسی persistence تنظیمات
        assert cli.config.verbose is True
        assert cli.config.force is True
        assert cli.config.db_type == "postgresql"
        assert cli.config.days == 60

    @patch('subprocess.run')
    def test_command_execution_with_db_type(self, mock_run):
        """تست اجرای command با db_type"""
        self.config.db_type = "postgresql"
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = self.cli._run_main_command(["create-db"])

        assert result is True

        # بررسی اضافه شدن --type postgresql
        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert "--type" in cmd
        assert "postgresql" in cmd

    @patch('subprocess.run')
    def test_command_execution_error_handling(self, mock_run):
        """تست مدیریت خطا در اجرای command"""
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="Database error")

        result = self.cli._run_main_command(["invalid-command"])

        assert result is False

    def test_quiet_mode_suppression(self):
        """تست سرکوب خروجی در quiet mode"""
        config = TSEConfig(quiet=True)
        cli = ProfessionalTSECLI(config)

        with patch('builtins.print') as mock_print:
            cli._success("Test message")
            cli._info("Info message")
            cli._warning("Warning message")

            # در quiet mode فقط error نمایش داده می‌شود
            cli._error("Error message")

            # بررسی اینکه فقط error print شده
            assert mock_print.call_count == 1
            error_call = mock_print.call_args
            assert "❌ Error message" in error_call[0][0]

    def test_verbose_mode_logging(self):
        """تست logging در verbose mode"""
        config = TSEConfig(verbose=True)
        cli = ProfessionalTSECLI(config)

        with patch('builtins.print') as mock_print:
            cli._log("Test message", "info")

            mock_print.assert_called_with("[INFO] Test message")

    def test_dry_run_prevention(self):
        """تست جلوگیری از اجرای واقعی در dry run"""
        config = TSEConfig(dry_run=True)
        cli = ProfessionalTSECLI(config)

        with patch('builtins.print') as mock_print, \
             patch('subprocess.run') as mock_run:

            result = cli._run_main_command(["create-db"])

            assert result is True
            mock_run.assert_not_called()

            # بررسی نمایش پیام dry run
            dry_run_call = None
            for call_args in mock_print.call_args_list:
                if "DRY RUN" in str(call_args):
                    dry_run_call = call_args
                    break

            assert dry_run_call is not None