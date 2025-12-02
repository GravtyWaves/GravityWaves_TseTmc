#!/usr/bin/env python3
"""
Professional TSE Data Collector CLI
Enterprise-grade unified command-line interface for TSE data collection, PostgreSQL management, and system setup
"""

import os
import sys
import argparse
import subprocess
import json
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass
import logging
import platform

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.logger import setup_logger

# Setup logger
logger = setup_logger()

@dataclass
class TSEConfig:
    """TSE CLI Configuration"""
    verbose: bool = False
    dry_run: bool = False
    force: bool = False
    quiet: bool = False
    db_type: str = "sqlite"
    days: int = 30
    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = "password"
    database: str = "tse_db"

class ProfessionalTSECLI:
    """Professional TSE Data Collector CLI"""

    def __init__(self, config: TSEConfig):
        self.config = config
        self.system = platform.system().lower()

    def _log(self, message: str, level: str = "info") -> None:
        """Log message with appropriate level"""
        if self.config.verbose or level in ["error", "warning"]:
            getattr(logger, level)(message)
            if not self.config.quiet:
                print(f"[{level.upper()}] {message}")

    def _success(self, message: str) -> None:
        """Print success message"""
        if not self.config.quiet:
            print(f"✅ {message}")

    def _error(self, message: str) -> None:
        """Print error message"""
        print(f"❌ {message}", file=sys.stderr)

    def _warning(self, message: str) -> None:
        """Print warning message"""
        if not self.config.quiet:
            print(f"⚠️  {message}")

    def _info(self, message: str) -> None:
        """Print info message"""
        if not self.config.quiet:
            print(f"ℹ️  {message}")

    def _confirm_action(self, action: str, target: str = "") -> bool:
        """Get user confirmation for dangerous actions"""
        if self.config.force:
            return True

        target_str = f" '{target}'" if target else ""
        response = input(f"Are you sure you want to {action}{target_str}? (yes/no): ")
        return response.lower() in ['yes', 'y']

    def _run_main_command(self, args: List[str]) -> bool:
        """Execute main.py command"""
        if self.config.dry_run:
            self._info(f"DRY RUN: Would execute: python main.py {' '.join(args)}")
            return True

        cmd = [sys.executable, "main.py"] + args

        if self.config.db_type != "sqlite":
            cmd.extend(["--type", self.config.db_type])

        self._log(f"Executing: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                cwd=project_root,
                capture_output=not self.config.verbose,
                text=True,
                timeout=3600  # 1 hour timeout
            )

            if result.returncode == 0:
                if result.stdout and not self.config.quiet:
                    print(result.stdout)
                return True
            else:
                self._error(f"Command failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            self._error("Command timed out after 1 hour")
            return False
        except Exception as e:
            self._error(f"Command execution failed: {e}")
            return False

    # === TSE Data Operations ===

    def setup_database(self) -> bool:
        """Setup database and load initial data"""
        db_name = "PostgreSQL" if self.config.db_type == "postgresql" else "SQLite"
        self._info(f"Setting up {db_name} database...")

        # Check PostgreSQL requirements
        if self.config.db_type == "postgresql":
            if not os.getenv("DATABASE_URL"):
                self._error("DATABASE_URL environment variable not set")
                self._info("Example: postgresql://user:password@localhost:5432/tse_db")
                return False

        # Create database
        if not self._run_main_command(["create-db"]):
            return False

        # Load initial data
        self._info("Loading initial data...")
        if not self._run_main_command(["load-initial-data"]):
            return False

        self._success(f"{db_name} database setup completed successfully")
        return True

    def load_initial_data(self) -> bool:
        """Load initial data into database"""
        self._info("Loading initial data into database...")
        return self._run_main_command(["load-initial-data"])

    def collect_initial_data(self) -> bool:
        """Collect fresh initial data from TSE API"""
        self._info("Collecting fresh initial data from TSE API...")

        # Collect sectors first
        self._info("Collecting sectors...")
        if not self._run_main_command(["update", "--mode", "sectors"]):
            return False

        # Collect stocks
        self._info("Collecting stocks...")
        if not self._run_main_command(["update", "--mode", "stocks"]):
            return False

        # Collect indices
        self._info("Collecting indices...")
        if not self._run_main_command(["update", "--mode", "indices"]):
            return False

        self._success("Fresh initial data collected successfully")
        return True

    def update_data(self, mode: str) -> bool:
        """Update data with specified mode"""
        mode_names = {
            "full": "complete dataset",
            "stocks": "stocks data",
            "sectors": "sectors data",
            "indices": "indices data",
            "prices": f"price history ({self.config.days} days)",
            "ri": f"RI history ({self.config.days} days)"
        }

        mode_name = mode_names.get(mode, mode)
        self._info(f"Updating {mode_name}...")

        args = ["update", "--mode", mode]
        if mode in ["prices", "ri"]:
            args.extend(["--days", str(self.config.days)])

        return self._run_main_command(args)

    def rebuild_table(self, table: str) -> bool:
        """Rebuild specific table"""
        table_names = {
            "stocks": "stocks table",
            "sectors": "sectors table",
            "indices": "indices table",
            "price_history": "price history table",
            "ri_history": "RI history table"
        }

        table_name = table_names.get(table, table)

        if not self._confirm_action(f"rebuild the {table_name}", table):
            self._info("Operation cancelled")
            return True

        self._info(f"Rebuilding {table_name}...")
        return self._run_main_command(["rebuild-table", "--table", table])

    def continuous_update(self, interval: int) -> bool:
        """Run continuous update"""
        self._info(f"Starting continuous update (interval: {interval}s)")
        self._warning("Press Ctrl+C to stop continuous update")

        return self._run_main_command(["continuous-update", "--interval", str(interval)])

    def show_status(self) -> bool:
        """Show system status"""
        try:
            # Check database connection
            db_status = "Unknown"
            if self.config.db_type == "postgresql":
                # Try to import and check PostgreSQL
                try:
                    from database.postgres_db import PostgreSQLDatabase
                    db = PostgreSQLDatabase()
                    session = db.get_session()
                    session.close()
                    db_status = "Connected"
                except Exception:
                    db_status = "Failed"
            else:
                # SQLite is always available
                db_status = "Available"

            # Get system info
            status = {
                "timestamp": datetime.now().isoformat(),
                "database": {
                    "type": self.config.db_type,
                    "status": db_status,
                    "url": os.getenv("DATABASE_URL", "Not set") if self.config.db_type == "postgresql" else "SQLite database"
                },
                "configuration": {
                    "verbose": self.config.verbose,
                    "dry_run": self.config.dry_run,
                    "force": self.config.force
                }
            }

            print("╔══════════════════════════════════════════════════════════════╗")
            print("║                   TSE Data Collector Status                  ║")
            print("╠══════════════════════════════════════════════════════════════╣")
            print(f"║ Database Type: {self.config.db_type:<47} ║")
            print(f"║ Database Status: {db_status:<45} ║")
            if self.config.db_type == "postgresql":
                db_url = os.getenv("DATABASE_URL", "Not set")
                print(f"║ Database URL: {db_url[:48]:<48} ║")
            print("╠══════════════════════════════════════════════════════════════╣")
            print(f"║ Verbose Mode: {str(self.config.verbose):<46} ║")
            print(f"║ Dry Run Mode: {str(self.config.dry_run):<46} ║")
            print(f"║ Force Mode: {str(self.config.force):<48} ║")
            print("╚══════════════════════════════════════════════════════════════╝")

            return True

        except Exception as e:
            self._error(f"Failed to get status: {e}")
            return False

def create_parser() -> argparse.ArgumentParser:
    """Create professional argument parser"""
    parser = argparse.ArgumentParser(
        prog="tse-cli",
        description="Professional TSE Data Collector CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Database Types:
  sqlite      SQLite database (default, file-based)
  postgresql  PostgreSQL database (requires DATABASE_URL)

Examples:
  tse-cli setup --db-type postgresql
  tse-cli update full --days 90 --verbose
  tse-cli rebuild stocks --force
  tse-cli continuous --interval 7200 --dry-run
  tse-cli status

For PostgreSQL operations, see: postgres-cli --help
        """
    )

    # Global options
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    parser.add_argument('--dry-run', '-n', action='store_true',
                       help='Show what would be done without executing')
    parser.add_argument('--force', '-f', action='store_true',
                       help='Force operations without confirmation')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Suppress non-error output')
    parser.add_argument('--db-type', choices=['sqlite', 'postgresql'], default='sqlite',
                       help='Database type (default: sqlite)')

    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Setup
    setup_parser = subparsers.add_parser('setup', help='Setup database and load initial data')
    setup_parser.add_argument('--db-type', choices=['sqlite', 'postgresql'], default='sqlite',
                             help='Database type for setup')

    # Update operations
    update_parser = subparsers.add_parser('update', help='Update data')
    update_parser.add_argument('mode', choices=['full', 'stocks', 'sectors', 'indices', 'prices', 'ri'],
                              help='Update mode')
    update_parser.add_argument('--days', type=int, default=30,
                              help='Number of days for history updates (default: 30)')

    # Rebuild operations
    rebuild_parser = subparsers.add_parser('rebuild', help='Rebuild specific table')
    rebuild_parser.add_argument('table', choices=['stocks', 'sectors', 'indices', 'price_history', 'ri_history'],
                               help='Table to rebuild')

    # Continuous update
    continuous_parser = subparsers.add_parser('continuous', help='Run continuous update')
    continuous_parser.add_argument('--interval', type=int, default=3600,
                                  help='Update interval in seconds (default: 3600)')

    # Status
    subparsers.add_parser('status', help='Show system status')

    # Collect initial data
    subparsers.add_parser('collect-initial', help='Collect fresh initial data from TSE API')

    # PostgreSQL-specific commands (only available when db-type is postgresql)
    check_parser = subparsers.add_parser('check-connection', help='Check PostgreSQL connection')

    backup_parser = subparsers.add_parser('backup', help='Backup PostgreSQL database')
    backup_parser.add_argument('file', help='Backup file path')
    backup_parser.add_argument('--compress', action='store_true', default=True,
                              help='Compress backup (default: True)')

    restore_parser = subparsers.add_parser('restore', help='Restore PostgreSQL database from backup')
    restore_parser.add_argument('file', help='Backup file path')

    info_parser = subparsers.add_parser('db-info', help='Show PostgreSQL database information')
    info_parser.add_argument('--format', choices=['table', 'json'], default='table',
                            help='Output format (default: table)')

    optimize_parser = subparsers.add_parser('optimize', help='Optimize PostgreSQL database')
    optimize_parser.add_argument('--full-vacuum', action='store_true',
                                help='Use VACUUM FULL instead of VACUUM ANALYZE')

    subparsers.add_parser('create-indexes', help='Create PostgreSQL performance indexes')

    query_parser = subparsers.add_parser('run-query', help='Execute custom SQL query')
    query_parser.add_argument('sql', help='SQL query to execute')
    query_parser.add_argument('--format', choices=['table', 'json'], default='table',
                             help='Output format (default: table)')
    query_parser.add_argument('--limit', type=int, default=50,
                             help='Limit number of rows displayed (default: 50)')

    env_parser = subparsers.add_parser('setup-env', help='Setup environment variables')
    env_parser.add_argument('--env-file', default='.env',
                           help='Environment file path (default: .env)')

    return parser

def main():
    """Professional main entry point"""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Create CLI configuration
    config = TSEConfig(
        verbose=args.verbose,
        dry_run=args.dry_run,
        force=args.force,
        quiet=args.quiet,
        db_type=getattr(args, 'db_type', 'sqlite'),
        days=getattr(args, 'days', 30)
    )

    # Override db_type for setup command
    if args.command == 'setup' and hasattr(args, 'db_type') and args.db_type:
        config.db_type = args.db_type

    # Initialize CLI
    cli = ProfessionalTSECLI(config)

    # Execute command
    success = False

    try:
        if args.command == 'setup':
            success = cli.setup_database()

        elif args.command == 'update':
            success = cli.update_data(args.mode)

        elif args.command == 'rebuild':
            success = cli.rebuild_table(args.table)

        elif args.command == 'continuous':
            success = cli.continuous_update(args.interval)

        elif args.command == 'status':
            success = cli.show_status()

        elif args.command == 'collect-initial':
            success = cli.collect_initial_data()

        elif args.command == 'check-connection':
            success = cli.check_connection()

        elif args.command == 'backup':
            success = cli.backup_database(args.file, args.compress)

        elif args.command == 'restore':
            success = cli.restore_database(args.file)

        elif args.command == 'db-info':
            success = cli.show_database_info(args.format)

        elif args.command == 'optimize':
            success = cli.optimize_database(args.full_vacuum)

        elif args.command == 'create-indexes':
            success = cli.create_indexes()

        elif args.command == 'run-query':
            success = cli.run_query(args.sql, args.format, args.limit)

        elif args.command == 'setup-env':
            success = cli.setup_environment(args.env_file)

        else:
            parser.print_help()
            sys.exit(1)

    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        if config.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

    if success:
        if not config.quiet:
            print(f"✅ Command '{args.command}' completed successfully")
        sys.exit(0)
    else:
        print(f"❌ Command '{args.command}' failed", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
