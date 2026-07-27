## Context

The current CLI implementation in `src/ocpp/__main__.py` is overly complex. It handles `.project` files, bootstrapping, and several command-line flags that are no longer necessary. This design outlines the simplification of the CLI to focus on its core functionality.

## Goals / Non-Goals

**Goals:**

-   Remove all code related to `.project` files from `src/ocpp/__main__.py`.
-   Delete the `src/ocpp/bootstrap.py` and `src/ocpp/project.py` modules.
-   Simplify the `ArgumentParser` to only include the `--preset` flag.
-   The execution flow will be:
    1.  Load API keys from `.env`.
    2.  Select OMO preset.
    3.  Activate Python venv.
-   Update all tests to reflect the simplified functionality.

**Non-Goals:**

-   Introducing any new functionality.
-   Changing the way OMO presets or venv detection works.

## Decisions

-   **Code Removal**: All functions, imports, and logic related to `.project` files, bootstrapping, and the removed CLI flags will be deleted from `src/ocpp/__main__.py`. This includes the `run_bootstrap`, `parse_project`, and related error handling.
-   **Module Deletion**: The `src/ocpp/bootstrap.py` and `src/ocpp/project.py` files will be deleted entirely, as their functionality is no longer needed.
-   **Test Simplification**: The `tests/test_bootstrap.py` and `tests/test_project.py` files will be deleted. The remaining tests will be updated to focus on the simplified CLI flow.

## Risks / Trade-offs

-   **Risk**: Removing the `.project` file functionality might affect users who were relying on it.
-   **Mitigation**: The proposal clearly states that this functionality is being removed and that users should use `.env` files instead. This is a planned breaking change.
