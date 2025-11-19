# Chronotag

**Chronotag** is a custom logging utility for Python that provides centralized logging configuration, automatic message prefixing, and specialized "beacon" logging for timing operations. It is designed to work seamlessly with Google Cloud Logging when available, falling back to standard logging otherwise.

## Features

-   **Prefixing**: Automatically prefix all log messages with a specific string (e.g., `[my-service]`).
-   **Beacons**: Special logging methods (`log_start`, `log_end`, `log_beacon`) to track the start, end, and duration of operations.
-   **Google Cloud Logging**: Optional integration with Google Cloud Logging.
-   **File Rotation**: Built-in support for rotating log files.

## Installation

You can install `chronotag` using `uv` or `pip`:

```bash
uv add chronotag
# or
pip install chronotag
```

*(Note: If installing from a local source, use `uv add .` or `pip install .`)*

## Usage

### Basic Logging

```python
import chronotag

# Initialize the logger
logger = chronotag.get_prefixed_logger(
    logger_name="my_app",
    prefix="APP-CORE"
)

logger.info("Application started")
# Output: [APP-CORE] Application started
```

### Beacon Logging (Timing)

Track the duration of operations using `log_start` and `log_end`.

```python
# Start a timer with a unique key
logger.log_start("db_query", "Starting database query...")

# ... perform operation ...

# End the timer (automatically calculates and logs elapsed time)
logger.log_end("db_query", "Query completed.")
# Output: [APP-CORE] (BEACON - [db_query] - END (Elapsed time 0.15 s)) Query completed.
```

### Single Beacon (Blip)

Log a significant event without timing.

```python
logger.log_beacon("milestone", "Reached checkpoint A")
# Output: [APP-CORE] (BEACON - [milestone] - BLIP) Reached checkpoint A
```

## Configuration

The `get_prefixed_logger` function accepts several arguments to configure logging behavior:

-   `logger_name` (str): Name of the logger.
-   `prefix` (str): String to prefix messages with.
-   `cloud_logger_name` (str, optional): Name for the Google Cloud Logging handler.
-   `enable_gcloud_logging` (bool, default=False): Enable Google Cloud Logging.
-   `log_file_path` (str, default="logs.txt"): Path to the log file.
-   `log_file_max_bytes` (int): Max size for log rotation.
-   `log_file_backup_count` (int): Number of backup files to keep.

## Testing

To run tests, use `pytest`:

```bash
uv run pytest
```

To run tests with coverage:

```bash
uv run pytest --cov=chronotag
```

To see which lines are not covered:

```bash
uv run pytest --cov=chronotag --cov-report=term-missing
```

## Roadmap / TODO

Future improvements planned for `chronotag`:

-   [ ] **Context Manager for Timing**: Implement a context manager (e.g., `with logger.measure(...)`) for cleaner timing code.
-   [ ] **Thread Safety**: Ensure `_start_times` and other mutable states are thread-safe.
-   [ ] **Type Hinting**: Add comprehensive type annotations and `mypy` support.
-   [ ] **Configuration Object**: Refactor `get_prefixed_logger` to accept a configuration object/dataclass.
-   [ ] **Structured Logging (JSON)**: Support JSON output for better integration with cloud logging systems.
-   [ ] **Decorator Support**: Add decorators for automatic function timing (e.g., `@logger.time_execution`).
-   [ ] **Explicit Exports**: Define `__all__` in `__init__.py` for a cleaner public API.

