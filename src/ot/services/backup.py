from datetime import datetime
from pathlib import Path

from ot.utils import DEFAULT_MAX_BACKUP_FILES, Logger


class BackupService:
    def __init__(
        self,
        state_path: Path,
        backup_dir: Path,
        log_level: int,
        max_backup_files: int | None = None,
    ) -> None:
        self.state_path = state_path
        self.backup_dir = backup_dir
        self.max_backup_files = max_backup_files or DEFAULT_MAX_BACKUP_FILES
        self.__logger = Logger("ot::BackupService", level=log_level)

    def set_max_backup_files(self, max_files: int) -> None:
        """Set the maximum number of backup files to keep.

        Args:
            max_files (int): The maximum number of backup files.
        """
        self.__logger.debug(
            f"setting max backup files from {self.max_backup_files} to {max_files}"
        )
        self.max_backup_files = max_files
        self.__logger.debug(f"max backup files set to {self.max_backup_files}")

    def cleanup_old_backups(self) -> None:
        """Remove old backup files exceeding the maximum limit."""
        self.__logger.debug("cleaning up old backup files...")
        backup_files = sorted(
            Path(self.backup_dir).glob("state*.json"),
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )
        self.__logger.debug(
            f"found {len(backup_files)} backup files, "
            f"max allowed is {self.max_backup_files}"
        )
        for old_file in backup_files[self.max_backup_files :]:
            self.__logger.debug(f"removing old backup file: {old_file!s}")
            try:
                old_file.unlink()
                self.__logger.debug(f"removed old backup file: {old_file!s}")
            except FileNotFoundError:
                # File may have been removed concurrently; log and continue.
                self.__logger.debug(
                    f"old backup file already missing during cleanup: {old_file!s}"
                )
        self.__logger.debug("old backup files cleanup complete.")

    def create_backup(self) -> Path | None:
        """Create a backup of the current state file.

        Returns:
            Path | None: The path to the created backup file, or None if backup failed.
        """
        self.__logger.debug("creating backup of state file...")
        backup_path = (
            self.backup_dir / f"state-{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
        )
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        try:
            self.state_path.copy(backup_path)
        except (FileNotFoundError, PermissionError, OSError) as e:
            self.__logger.warning(f"failed to create backup: {e}")
            return None

        self.cleanup_old_backups()
        self.__logger.debug(f"backup created at: {backup_path!s}")
        return backup_path
