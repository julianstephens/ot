## v0.1.2

- Adds `ot doctor` to assist with diagnosing and fixing storage file issues

## v0.1.1

- Renames global `--verbose` to `--debug`
- Adds prompt to `ot today` if no commitment is set for the current day
- Adds aliases for common commands
- Bumps storage schema to `v2`
    - Adds `note` field to commitment entries
    - Adds global `settings` to stored data
        - Adds support for `prompt_on_empty` for missing commitments
        - Adds support for `default_log_days` for log window constraints
        - Adds support for `strict_mode` for enforcing stricter rules (no editing after done/skip, limited future dates, etc.)
- Adds `ot note <message> [--date/-d]`
- Adds `ot config <subcommand>` module for managing settings
- Adds `ot edit <new title>` for updating commitment titles
- Adds test coverage

## v0.1.0

- Add `ot` CLI
