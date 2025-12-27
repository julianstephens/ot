# Custom Agent

## Dev environment tips
- Run `uv sync` to install dependencies and create an virtual environment with a managed python installation.
- Run `uvx ruff check --fix` to run the linter for the project.
- Run `uvx ruff format` to format files.

## Testing instructions
- Run `pytest` to run tests for the entire project.
- Add or update tests for the code you change, even if nobody asked.

## PR instructions
- Title format: [<project_name>] <Title>
- Always run `uvx ruff check --fix` and `pytest` before committing.