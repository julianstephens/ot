from pathlib import Path

import msgspec
from tzlocal import get_localzone

from ot.utils import (
    DATE_FORMAT,
    DEFAULT_LOG_DAYS,
    DEFAULT_MAX_BACKUP_FILES,
    STATE_VERSION,
    Day,
    DoctorResult,
    InvalidDateStringError,
    Logger,
    Remedy,
    Settings,
    State,
    Status,
    validate_date_string,
)

from .backup import BackupService


class DoctorService:
    def __init__(self, state_path: Path, backup_dir: Path, log_level: int) -> None:
        self.state_path = state_path
        self.backup_dir = backup_dir
        self.__backup_svc = BackupService(
            state_path=state_path,
            backup_dir=backup_dir,
            log_level=log_level,
        )
        self.__logger = Logger("ot::DoctorService", level=log_level)

    def run(self) -> DoctorResult:
        """Run the doctor service to diagnose and repair state file issues.

        Exit codes:
            0: No issues found or all issues auto-fixed.
            1: Non-critical issues found that may require manual intervention.
            2: Critical issues found; manual intervention required.
            3: State file missing; initialization required.

        Returns:
            DoctorResult: The result of the doctor service run.
        """
        result = DoctorResult()

        self.__logger.debug("starting state file diagnostics...")

        if not self._check_integrity(result):
            return result

        self.__logger.debug("loading and validating state file structure...")
        state = self._load_and_validate_structure(result)
        if state is None:
            return result

        modified = self._repair_semantics(state, result)
        if modified:
            self.__logger.debug("modifications made to state, creating backup...")
            bp = self.__backup_svc.create_backup()
            result.backup_path = bp
            self.__logger.debug("saving repaired state file...")
            self._save_state(state)
            self.__logger.debug("repaired state file saved.")

        modified_days = self._repair_days(state, result)
        if modified_days:
            if not modified:
                bp = self.__backup_svc.create_backup()
                result.backup_path = bp
            self.__logger.debug("saving repaired state file with day fixes...")
            self._save_state(state)
            self.__logger.debug("repaired state file saved with day fixes.")

        return result

    def _save_state(self, state: State) -> None:
        """Save the state to the state file.

        Args:
            state (State): The state object to save.
        """
        self.__logger.debug("saving state file...")
        with self.state_path.open("wb") as f:
            f.write(msgspec.json.encode(state))
        self.__logger.debug("state file saved.")

    def _check_integrity(self, result: DoctorResult) -> bool:
        """Check the integrity of the state file.

        Returns:
            bool: True if the state file passes integrity checks.
        """
        self.__logger.debug("checking state file integrity...")
        if not self.state_path.exists():
            self.__logger.debug("state file does not exist")
            result.exit_code = 3
            result.remedy = Remedy.INIT_STORAGE
            return False
        if self.state_path.stat().st_size == 0:
            self.__logger.debug("state file is empty")
            result.exit_code = 1
            result.remedy = Remedy.LOAD_STATE
            return False

        with self.state_path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    return True

        self.__logger.debug("state file is empty")
        result.exit_code = 1
        result.remedy = Remedy.LOAD_STATE
        return False

    def _load_and_validate_structure(self, result: DoctorResult) -> State | None:
        """Load and validate the structure of the state file.

        Args:
            result (DoctorResult): The result object to record validation information.

        Returns:
            State | None: The loaded State object if valid, else None.
        """
        state = None
        data = b""
        try:
            self.__logger.debug("validating state file structure...")
            with self.state_path.open("rb") as f:
                data = f.read()
            state = msgspec.json.decode(data, type=State)
            self.__logger.debug("state file structure valid")
        except msgspec.ValidationError as ex:
            try:
                self.__logger.debug(
                    "strict validation failed, attempting loose load..."
                )
                raw_data = msgspec.json.decode(data)
                state = State(
                    timezone=raw_data.get("timezone"),
                    days={},
                    version=raw_data.get("version", 1),
                    settings=None,
                )
                assert state.days is not None

                # Handle settings if present
                if "settings" in raw_data and isinstance(raw_data["settings"], dict):
                    s_data = raw_data["settings"]
                    state.settings = Settings(
                        auto_prompt_on_empty=s_data.get("auto_prompt_on_empty", True),
                        strict_mode=s_data.get("strict_mode", True),
                        default_log_days=s_data.get(
                            "default_log_days", DEFAULT_LOG_DAYS
                        ),
                        max_backup_files=s_data.get(
                            "max_backup_files", DEFAULT_MAX_BACKUP_FILES
                        ),
                    )

                # Handle days if present
                if "days" in raw_data and isinstance(raw_data["days"], dict):
                    for d_date, d_data in raw_data["days"].items():
                        if isinstance(d_data, dict):
                            # Attempt to create Day object
                            try:
                                # Try to fix status casing immediately if possible
                                status_val = d_data.get("status")
                                if isinstance(status_val, str):
                                    try:
                                        # Try exact match
                                        status = Status(status_val)
                                    except ValueError:
                                        try:
                                            # Try case-insensitive match
                                            status = Status(status_val.lower())
                                            result.autofixed.append(
                                                f"Corrected status for date '{d_date}' "
                                                f"to '{status}'."
                                            )
                                        except ValueError:
                                            # If still invalid, skip this day and
                                            # report it as unresolved
                                            result.unresolved.append(
                                                f"Invalid status '{status_val}' for "
                                                f"date '{d_date}'"
                                            )
                                            continue
                                else:
                                    status = Status.PENDING

                                day = Day(
                                    title=d_data.get("title", ""),
                                    status=status,
                                    note=d_data.get("note"),
                                    created_at=d_data.get("created_at"),
                                    completed_at=d_data.get("completed_at"),
                                    skipped_at=d_data.get("skipped_at"),
                                )
                                state.days[d_date] = day
                            except Exception as e:
                                result.unresolved.append(
                                    f"Could not load day '{d_date}': {e}"
                                )
            except Exception:
                pass
            else:
                self.__logger.debug("loose load successful, proceeding with repairs")
                result.exit_code = 0
                result.remedy = None
                return state

            self.__logger.debug(
                f"state file structure invalid, validation error: {ex!s}"
            )
            result.remedy = Remedy.FORCE_INIT_STORAGE
            result.exit_code = 2
            result.unresolved.append(f"Validation error: {ex!s}")
        except msgspec.DecodeError as ex:
            self.__logger.debug(f"state file structure invalid, decode error: {ex!s}")
            result.remedy = Remedy.FORCE_INIT_STORAGE
            result.exit_code = 2
            result.unresolved.append(f"Decode error: {ex!s}")

        return state

    def _repair_semantics(self, state: State, result: DoctorResult) -> bool:
        """Repair semantic issues in the state file.

        Args:
            state (State): The state object to repair.
            result (DoctorResult): The result object to record repair information.

        Returns:
            bool: True if the state was modified, False otherwise.
        """
        modified = False

        if state.version < STATE_VERSION:
            self.__logger.debug(
                f"state version {state.version} is older than current "
                f"version {STATE_VERSION}, migration needed"
            )
            result.unresolved.append(
                f"State version {state.version} is older than current "
                f"version {STATE_VERSION}, migration needed."
            )
            result.remedy = Remedy.MIGRATE_STATE
            result.exit_code = 1
            return False

        settings = state.settings
        if settings is None:
            self.__logger.debug("settings field missing, initializing default settings")
            state.settings = Settings()
            result.autofixed.append("Settings field was missing, initialized default.")
            modified = True
        else:
            self.__logger.debug("settings field present. validating fields...")

        timezone = state.timezone
        if timezone is None or timezone.strip() == "":
            self.__logger.debug(
                "timezone field missing or empty, setting default value"
            )
            iana_timezone = get_localzone()
            state.timezone = str(iana_timezone)
            result.autofixed.append(
                f"timezone field was missing or empty, set to system timezone "
                f"'{iana_timezone}'."
            )
            modified = True
        return modified

    def _repair_days(self, state: State, result: DoctorResult) -> bool:
        def _validate_date_or_raise(date_str: str) -> str:
            validated_date = validate_date_string(date_str)
            if validated_date is None:
                raise InvalidDateStringError(
                    date_string=date_str, format_code=DATE_FORMAT
                )
            return validated_date

        modified = False

        if state.days is None:
            state.days = {}

        for date_str, day in list(state.days.items()):
            try:
                _validate_date_or_raise(date_str)
            except Exception as ex:
                self.__logger.debug(
                    f"invalid date string '{date_str}' in days, removing entry"
                )
                result.autofixed.append(
                    f"Removed day with invalid date string '{date_str}': {ex!s}"
                )
                del state.days[date_str]
                modified = True
                continue

            # Validate and repair day status
            try:
                Status(day.status.value)
            except ValueError:
                try:
                    status = Status(day.status.value.lower())
                    self.__logger.debug(
                        f"correcting status '{day.status}' to '{status}' for date "
                        f"'{date_str}'"
                    )
                    day.status = status
                    state.days[date_str] = day
                    modified = True
                    result.autofixed.append(
                        f"Corrected status for date '{date_str}' to '{status}'."
                    )
                except ValueError:
                    self.__logger.debug(
                        f"invalid status '{day.status}' for date '{date_str}', "
                        f"leaving unchanged and marking as unresolved"
                    )
                    result.unresolved.append(
                        f"Invalid status '{day.status}' for date '{date_str}', not auto-corrected"
                    )

            # Validate and repair timestamps
            if day.status == Status.DONE and day.completed_at is None:
                self.__logger.debug(
                    f"completed_at missing for DONE day '{date_str}', setting to None"
                )
                modified = True
                result.autofixed.append(
                    f"Set completed_at for DONE day on '{date_str}'"
                )

            if day.status == Status.SKIPPED and day.skipped_at is None:
                self.__logger.debug(
                    f"skipped_at missing for SKIPPED day '{date_str}', setting to None"
                )
                modified = True
                result.autofixed.append(
                    f"Set skipped_at for SKIPPED day on '{date_str}'"
                )

            # created_at is also nullable
            if day.created_at is None:
                self.__logger.debug(
                    f"day for date '{date_str}' missing created_at, setting to null"
                )
                modified = True
                result.autofixed.append(
                    f"Set created_at for day on '{date_str}' to null."
                )

            # Validate and repair titles
            if not day.title.strip():
                self.__logger.debug(f"day for date '{date_str}' missing title")
                result.unresolved.append(
                    f"Day for date '{date_str}' is missing a title."
                )
            if day.title.endswith(" "):
                self.__logger.debug(
                    f"day for date '{date_str}' has title with trailing spaces, "
                    f"trimming"
                )
                day.title = day.title.rstrip()
                state.days[date_str] = day
                modified = True
                result.autofixed.append(
                    f"Trimmed trailing spaces from title for day on '{date_str}'."
                )

            # Validate and repair notes
            if day.note is not None and day.note.strip() == "":
                self.__logger.debug(
                    f"day for date '{date_str}' has invalid note type, setting to None"
                )
                day.note = None
                state.days[date_str] = day
                modified = True
                result.autofixed.append(
                    f"Set note for day on '{date_str}' to null due to invalid type."
                )
            if day.note and day.note.endswith(" "):
                self.__logger.debug(
                    f"day for date '{date_str}' has note with trailing spaces, trimming"
                )
                day.note = day.note.rstrip()
                state.days[date_str] = day
                modified = True
                result.autofixed.append(
                    f"Trimmed trailing spaces from note for day on '{date_str}'."
                )

        return modified
