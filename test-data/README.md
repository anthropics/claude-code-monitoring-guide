# Test Data Directory

Contains test files and sample data for validating the monitoring system.

## Test Files
- **[`test-compaction.txt`](test-compaction.txt)** - Test data for compaction metrics
- **[`test-debug.txt`](test-debug.txt)** - Debug test scenarios
- **[`test-hook-data.txt`](test-hook-data.txt)** - Sample hook JSON data
- **[`test-write-hook.txt`](test-write-hook.txt)** - Write hook test data

## Usage

These files are used by the testing system:
```bash
just test all          # Uses test data automatically
just test hooks        # Validates hook processing with sample data
```

The test data helps validate:
- Hook JSON parsing
- Metric generation
- Data flow end-to-end
- Error handling scenarios