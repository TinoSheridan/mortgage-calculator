#!/usr/bin/env python3
"""Backup script for the mortgage calculator application."""
import datetime
import json
import logging
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path


class BackupManager:
    def __init__(self, config_path=None):
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.logger = self._setup_logging()
        self.config = self._load_config(config_path)

    def _setup_logging(self):
        """Configure logging for backup operations."""
        logger = logging.getLogger("backup_manager")
        logger.setLevel(logging.INFO)

        # Create handlers
        console_handler = logging.StreamHandler()
        file_handler = logging.FileHandler("logs/backup.log")

        # Create formatters and add it to handlers
        log_format = "%(asctime)s [%(levelname)s] %(message)s"
        formatter = logging.Formatter(log_format)
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        # Add handlers to the logger
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

        return logger

    def _load_config(self, config_path):
        """Load backup configuration."""
        if config_path is None:
            config_path = "config/production.py"

        # Import config from production.py
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from config.production import ProductionConfig

        return ProductionConfig

    def _create_backup_dir(self):
        """Create backup directory if it doesn't exist."""
        os.makedirs(self.config.BACKUP_DIR, exist_ok=True)

    def _cleanup_old_backups(self):
        """Remove backups older than retention period."""
        self.logger.info("Cleaning up old backups...")
        retention_days = self.config.BACKUP_RETENTION_DAYS
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=retention_days)

        for backup_file in Path(self.config.BACKUP_DIR).glob("*.tar.gz"):
            try:
                file_date = datetime.datetime.strptime(backup_file.stem.split("_")[0], "%Y%m%d")
                if file_date < cutoff_date:
                    self.logger.info(f"Removing old backup: {backup_file}")
                    backup_file.unlink()
            except (ValueError, IndexError):
                self.logger.warning(f"Skipping file with invalid name format: {backup_file}")

    def create_backup(self):
        """Create a new backup."""
        try:
            self._create_backup_dir()
            backup_name = f"mortgage_calc_backup_{self.timestamp}.tar.gz"
            backup_path = os.path.join(self.config.BACKUP_DIR, backup_name)

            self.logger.info(f"Creating backup: {backup_name}")

            with tarfile.open(backup_path, "w:gz") as tar:
                # Backup configuration files
                tar.add("config", arcname="config")
                tar.add("mortgage_config.json", arcname="mortgage_config.json")

                # Backup templates
                tar.add("templates", arcname="templates")

                # Backup application files
                tar.add("app.py", arcname="app.py")
                tar.add(
                    "Enhanced_Mortgage_Calculator.py",
                    arcname="Enhanced_Mortgage_Calculator.py",
                )
                tar.add("config_manager.py", arcname="config_manager.py")
                tar.add("security_config.py", arcname="security_config.py")

                # Backup logs (if they exist)
                if os.path.exists("logs"):
                    tar.add("logs", arcname="logs")

            # Create checksum
            checksum = subprocess.run(
                ["shasum", "-a", "256", backup_path], capture_output=True, text=True
            ).stdout.split()[0]

            # Save checksum
            checksum_file = f"{backup_path}.sha256"
            with open(checksum_file, "w") as f:
                f.write(checksum)

            self.logger.info(f"Backup created successfully: {backup_path}")
            self.logger.info(f"Checksum: {checksum}")

            # Cleanup old backups
            self._cleanup_old_backups()

            return True

        except Exception as e:
            self.logger.error(f"Backup failed: {str(e)}")
            return False


def main():
    backup_manager = BackupManager()
    success = backup_manager.create_backup()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
