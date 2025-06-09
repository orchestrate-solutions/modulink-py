# Changelog

All notable changes to ModuLink Python will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] (BREAKING CHANGES) - 2025-06-09

### Added
- Major refactor with enhanced Chain architecture
- Timezone-aware timestamps (Python 3.13+ compatibility)
- Comprehensive testing infrastructure (236 tests)

### Changed
- Migrated from `datetime.utcnow()` to `datetime.now(timezone.utc)`
- Streamlined connection handlers with proper error handling
- Enhanced type safety and consistency across modules

### Removed
- Obsolete documentation and example files
- Duplicate utility modules and backup files

### Fixed
- DateTime deprecation warnings
- Test failures related to timezone handling
- AttributeError issues with datetime.UTC


## [Unreleased]

### Added
- **Immutable Context Pattern Support** - Major new feature enabling functional programming approaches
  - Added `with_data()` method for immutable data updates (supports both dict and key-value formats)
  - Added `with_result()` method for immutable result merging into main data
  - Added `with_body()` method for setting request body data
  - Added `with_params()` method for setting parameter data
  - Added `start_step()` and `end_step()` immutable versions for step tracking
  - Added `add_error()` immutable version for error handling
  - Full backward compatibility with existing mutable patterns
  - Comprehensive test coverage for all immutable operations
  - Performance benchmarking showing ~2.7x overhead for immutable operations

### Enhanced
- **Context Class** - Migrated to hybrid immutable/mutable pattern
  - `_copy()` method now properly handles deep copying of all attributes
  - Immutable helper methods create new Context instances instead of mutating existing ones
  - Error handling maintains consistency between `error` attribute and `_errors` list
  - Step tracking works seamlessly with immutable pattern
  - Async support maintained for all immutable operations

### Documentation
- Added comprehensive [Immutable Patterns Guide](docs/immutable-patterns.md)
- Updated README.md with immutable pattern examples and benefits
- Created example files showcasing immutable patterns:
  - `examples/immutable_example.py` - Basic immutable pattern demonstrations
  - `examples/advanced_immutable_example.py` - Advanced patterns and performance analysis
  - Updated `examples/basic_example.py` with immutable pattern examples

### Testing
- Added `test_immutable_chain.py` - Comprehensive test suite for immutable patterns
- All existing tests pass, ensuring backward compatibility
- Added performance benchmarking for mutable vs immutable operations
- Added async execution tests with immutable contexts

### Fixed
- Fixed `setattr()` call in `_copy()` method that was missing attribute name parameter
- Enhanced error handling to maintain consistency across immutable operations
- **Resolved Deprecation Warnings**: Fixed `datetime.utcnow()` deprecation warnings by migrating to `datetime.now(timezone.utc)`
  - Updated all timestamp generation in Context class
  - Maintains ISO format compatibility  
  - Improved timezone awareness
- Improved memory management with proper deep copying of context attributes

## [Previous Version]
- Initial implementation of ModuLink Python with mutable Context patterns
- Function registration and chaining
- Trigger system (HTTP, Cron, CLI, Message)
- Middleware support
- Step timing and error tracking
- JSON serialization/deserialization
