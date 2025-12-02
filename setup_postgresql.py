#!/usr/bin/env python3
"""
Professional PostgreSQL Setup Script for TSE Data Collector
Enterprise-grade PostgreSQL installation and configuration tool
"""

import os
import sys
import argparse
import subprocess
import platform
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import logging

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.logger import setup_logger

# Setup logger
logger = setup_logger()

@dataclass
class PostgreSQLConfig:
    """PostgreSQL Configuration"""
    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = "password"
    database: str = "tse_db"
    install_deps: bool = True
    create_db: bool = True
    create_env_file: bool = True
    create_config_file: bool = True

class ProfessionalPostgreSQLSetup:
    """Professional PostgreSQL Setup Manager"""

    def __init__(self, config: PostgreSQLConfig, verbose: bool = False, dry_run: bool = False):
        self.config = config
        self.verbose = verbose
        self.dry_run = dry_run
        self.system = platform.system().lower()

    def _log(self, message: str, level: str = "info") -> None:
        """Log message with appropriate level"""
        if self.verbose or level in ["error", "warning"]:
            getattr(logger, level)(message)
            print(f"[{level.upper()}] {message}")

    def _success(self, message: str) -> None:
        """Print success message"""
        print(f"✅ {message}")

    def _error(self, message: str) -> None:
        """Print error message"""
        print(f"❌ {message}", file=sys.stderr)

    def _warning(self, message: str) -> None:
        """Print warning message"""
        print(f"⚠️  {message}")

    def _info(self, message: str) -> None:
        """Print info message"""
        print(f"ℹ️  {message}")

    def check_postgresql_installed(self) -> bool:
        """Check if PostgreSQL is installed"""
        self._info("Checking PostgreSQL installation...")

        try:
            result = subprocess.run(
                ['psql', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                version = result.stdout.strip().split()[-1]
                self._success(f"PostgreSQL {version} is installed")
                return True
            else:
                self._error("PostgreSQL check failed")
                return False
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self._error("PostgreSQL is not installed or not in PATH")
            return False

    def check_pg_dump_installed(self) -> bool:
        """Check if pg_dump is available"""
        try:
            result = subprocess.run(
                ['pg_dump', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def install_postgresql_linux(self) -> bool:
        """Install PostgreSQL on Linux"""
        self._info("Installing PostgreSQL on Linux...")

        if self.dry_run:
            self._info("DRY RUN: Would install PostgreSQL on Linux")
            return True

        try:
            # Detect package manager
            if shutil.which('apt'):
                # Ubuntu/Debian
                cmds = [
                    ['sudo', 'apt', 'update'],
                    ['sudo', 'apt', 'install', '-y', 'postgresql', 'postgresql-contrib', 'postgresql-client']
                ]
            elif shutil.which('yum'):
                # CentOS/RHEL
                cmds = [
                    ['sudo', 'yum', 'install', '-y', 'postgresql-server', 'postgresql-contrib']
                ]
            elif shutil.which('dnf'):
                # Fedora
                cmds = [
                    ['sudo', 'dnf', 'install', '-y', 'postgresql-server', 'postgresql-contrib']
                ]
            else:
                self._error("Unsupported Linux distribution")
                return False

            for cmd in cmds:
                self._log(f"Running: {' '.join(cmd)}")
                result = subprocess.run(cmd, check=True, capture_output=not self.verbose)
                if result.returncode != 0:
                    self._error(f"Command failed: {' '.join(cmd)}")
                    return False

            self._success("PostgreSQL installed successfully on Linux")
            return True

        except subprocess.CalledProcessError as e:
            self._error(f"Installation failed: {e}")
            return False

    def install_postgresql_macos(self) -> bool:
        """Install PostgreSQL on macOS"""
        self._info("Installing PostgreSQL on macOS...")

        if self.dry_run:
            self._info("DRY RUN: Would install PostgreSQL on macOS")
            return True

        try:
            # Check if Homebrew is installed
            if not shutil.which('brew'):
                self._error("Homebrew is not installed. Please install Homebrew first:")
                self._info("https://brew.sh/")
                return False

            cmds = [
                ['brew', 'update'],
                ['brew', 'install', 'postgresql']
            ]

            for cmd in cmds:
                self._log(f"Running: {' '.join(cmd)}")
                result = subprocess.run(cmd, check=True, capture_output=not self.verbose)
                if result.returncode != 0:
                    self._error(f"Command failed: {' '.join(cmd)}")
                    return False

            self._success("PostgreSQL installed successfully on macOS")
            return True

        except subprocess.CalledProcessError as e:
            self._error(f"Installation failed: {e}")
            return False

    def install_postgresql_windows(self) -> bool:
        """Install PostgreSQL on Windows"""
        self._info("PostgreSQL installation on Windows...")

        if self.dry_run:
            self._info("DRY RUN: Would prompt for PostgreSQL installation on Windows")
            return True

        self._warning("PostgreSQL installation on Windows must be done manually")
        self._info("Please download and install PostgreSQL from:")
        self._info("https://www.postgresql.org/download/windows/")
        self._info("After installation, run this script again to continue setup")

        return False  # Manual installation required

    def install_postgresql(self) -> bool:
        """Install PostgreSQL based on platform"""
        if self.system == "linux":
            return self.install_postgresql_linux()
        elif self.system == "darwin":
            return self.install_postgresql_macos()
        elif self.system == "windows":
            return self.install_postgresql_windows()
        else:
            self._error(f"Unsupported platform: {self.system}")
            return False

    def install_python_dependencies(self) -> bool:
        """Install Python dependencies for PostgreSQL"""
        if not self.config.install_deps:
            self._info("Skipping Python dependencies installation")
            return True

        self._info("Installing Python dependencies for PostgreSQL...")

        if self.dry_run:
            self._info("DRY RUN: Would install Python dependencies")
            return True

        packages = [
            'psycopg2-binary',
            'sqlalchemy',
            'python-dotenv'
        ]

        try:
            for package in packages:
                self._log(f"Installing {package}...")
                result = subprocess.run(
                    [sys.executable, '-m', 'pip', 'install', package],
                    check=True,
                    capture_output=not self.verbose
                )
                if result.returncode != 0:
                    self._error(f"Failed to install {package}")
                    return False

            self._success("Python dependencies installed successfully")
            return True

        except subprocess.CalledProcessError as e:
            self._error(f"Python dependencies installation failed: {e}")
            return False

    def create_database(self) -> bool:
        """Create PostgreSQL database"""
        if not self.config.create_db:
            self._info("Skipping database creation")
            return True

        self._info(f"Creating PostgreSQL database '{self.config.database}'...")

        if self.dry_run:
            self._info("DRY RUN: Would create PostgreSQL database")
            return True

        try:
            # Create database command
            cmd = [
                'createdb',
                '-h', self.config.host,
                '-p', str(self.config.port),
                '-U', self.config.user,
                self.config.database
            ]

            # Set environment
            env = os.environ.copy()
            env['PGPASSWORD'] = self.config.password

            self._log(f"Running: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=not self.verbose,
                text=True
            )

            if result.returncode == 0:
                self._success(f"Database '{self.config.database}' created successfully")
                return True
            else:
                # Check if database already exists
                if "already exists" in result.stderr:
                    self._warning(f"Database '{self.config.database}' already exists")
                    return True
                else:
                    self._error(f"Database creation failed: {result.stderr}")
                    return False

        except subprocess.CalledProcessError as e:
            self._error(f"Database creation failed: {e}")
            return False

    def create_env_file(self) -> bool:
        """Create .env file with PostgreSQL configuration"""
        if not self.config.create_env_file:
            self._info("Skipping .env file creation")
            return True

        self._info("Creating .env configuration file...")

        if self.dry_run:
            self._info("DRY RUN: Would create .env file")
            return True

        env_content = f"""# PostgreSQL Configuration for TSE Data Collector
# Generated by setup-postgresql script

# Database Connection
POSTGRES_HOST={self.config.host}
POSTGRES_PORT={self.config.port}
POSTGRES_USER={self.config.user}
POSTGRES_PASSWORD={self.config.password}
POSTGRES_DB={self.config.database}

# Database URL
DATABASE_URL=postgresql://{self.config.user}:{self.config.password}@{self.config.host}:{self.config.port}/{self.config.database}
DATABASE_TYPE=postgresql

# Application Settings
LOG_LEVEL=INFO
LOG_FILE=tse_collector.log
"""

        env_file = project_root / ".env"
        try:
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(env_content)

            self._success(f"Environment file created: {env_file}")
            self._warning("Please review and update the .env file with your actual credentials")
            return True

        except Exception as e:
            self._error(f"Failed to create .env file: {e}")
            return False

    def create_config_file(self) -> bool:
        """Create PostgreSQL configuration file"""
        if not self.config.create_config_file:
            self._info("Skipping config file creation")
            return True

        self._info("Creating PostgreSQL configuration file...")

        if self.dry_run:
            self._info("DRY RUN: Would create config file")
            return True

        config_content = f"""# PostgreSQL Configuration for TSE Data Collector
# Generated by setup-postgresql script

# Connection Settings
host = {self.config.host}
port = {self.config.port}
user = {self.config.user}
password = {self.config.password}
database = {self.config.database}

# Performance Settings
max_connections = 20
idle_timeout = 300
connection_pool_size = 10

# Backup Settings
backup_enabled = true
backup_path = ./backups
backup_interval_hours = 24
backup_retention_days = 30

# Logging Settings
log_level = INFO
log_file = postgresql.log
log_max_size = 10MB
log_backup_count = 5

# Security Settings
ssl_mode = prefer
ssl_cert_file =
ssl_key_file =
"""

        config_file = project_root / "postgresql.conf"
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(config_content)

            self._success(f"Configuration file created: {config_file}")
            return True

        except Exception as e:
            self._error(f"Failed to create config file: {e}")
            return False

    def test_connection(self) -> bool:
        """Test PostgreSQL connection"""
        self._info("Testing PostgreSQL connection...")

        if self.dry_run:
            self._info("DRY RUN: Would test PostgreSQL connection")
            return True

        try:
            cmd = [
                'psql',
                '-h', self.config.host,
                '-p', str(self.config.port),
                '-U', self.config.user,
                '-d', self.config.database,
                '-c', 'SELECT version();'
            ]

            env = os.environ.copy()
            env['PGPASSWORD'] = self.config.password

            result = subprocess.run(
                cmd,
                env=env,
                capture_output=not self.verbose,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                self._success("PostgreSQL connection test successful")
                return True
            else:
                self._error(f"Connection test failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            self._error("Connection test timed out")
            return False
        except Exception as e:
            self._error(f"Connection test failed: {e}")
            return False

    def run_setup(self) -> bool:
        """Run complete PostgreSQL setup"""
        self._info("=== Starting Professional PostgreSQL Setup ===")

        steps = [
            ("Check PostgreSQL installation", self.check_postgresql_installed),
            ("Install PostgreSQL", self.install_postgresql),
            ("Install Python dependencies", self.install_python_dependencies),
            ("Create database", self.create_database),
            ("Create .env file", self.create_env_file),
            ("Create config file", self.create_config_file),
            ("Test connection", self.test_connection),
        ]

        completed_steps = 0
        total_steps = len(steps)

        for step_name, step_func in steps:
            self._info(f"Step {completed_steps + 1}/{total_steps}: {step_name}")
            if step_func():
                completed_steps += 1
            else:
                self._error(f"Setup failed at step: {step_name}")
                return False

        self._success("=== PostgreSQL Setup Completed Successfully ===")
        self.print_next_steps()
        return True

    def print_next_steps(self) -> None:
        """Print next steps for user"""
        print("\n" + "="*60)
        print("🎉 PostgreSQL Setup Complete!")
        print("="*60)
        print("\nNext steps:")
        print("1. Review and update .env file with your credentials")
        print("2. Start PostgreSQL service if not running:")
        if self.system == "linux":
            print("   sudo systemctl start postgresql")
        elif self.system == "darwin":
            print("   brew services start postgresql")
        elif self.system == "windows":
            print("   Start PostgreSQL from Services panel")
        print("3. Run: tse-cli setup --db-type postgresql")
        print("4. Run: postgres-cli indexes")
        print("5. Run: tse-cli update full")
        print("\nFor help, see: CLI_GUIDE.md")
        print("="*60)

def create_parser() -> argparse.ArgumentParser:
    """Create professional argument parser"""
    parser = argparse.ArgumentParser(
        prog="setup-postgresql",
        description="Professional PostgreSQL Setup for TSE Data Collector",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  setup-postgresql
  setup-postgresql --host localhost --port 5432 --user postgres --password mypass
  setup-postgresql --no-create-db --verbose
  setup-postgresql --dry-run

For more information, see: CLI_GUIDE.md
        """
    )

    # Connection settings
    parser.add_argument('--host', default='localhost',
                       help='PostgreSQL host (default: localhost)')
    parser.add_argument('--port', type=int, default=5432,
                       help='PostgreSQL port (default: 5432)')
    parser.add_argument('--user', default='postgres',
                       help='PostgreSQL username (default: postgres)')
    parser.add_argument('--password', default='password',
                       help='PostgreSQL password (default: password)')
    parser.add_argument('--database', default='tse_db',
                       help='Database name (default: tse_db)')

    # Setup options
    parser.add_argument('--no-install-deps', action='store_true',
                       help='Skip Python dependencies installation')
    parser.add_argument('--no-create-db', action='store_true',
                       help='Skip database creation')
    parser.add_argument('--no-env-file', action='store_true',
                       help='Skip .env file creation')

    # Execution options
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    parser.add_argument('--dry-run', '-n', action='store_true',
                       help='Show what would be done without executing')

    return parser

def main():
    """Professional main entry point"""
    parser = create_parser()
    args = parser.parse_args()

    # Create configuration
    config = PostgreSQLConfig(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        database=args.database,
        install_deps=not args.no_install_deps,
        create_db=not args.no_create_db,
        create_env_file=not args.no_env_file,
        create_config_file=True  # Always create config file
    )

    # Initialize setup
    setup = ProfessionalPostgreSQLSetup(config, args.verbose, args.dry_run)

    # Run setup
    success = setup.run_setup()

    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
