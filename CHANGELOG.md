# Changelog

## [4.0.3] - 2025-06-27

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


## [4.0.2] - 2025-06-27
### Fixed
- Export HttpListener and TcpListener in public API (previously only BaseListener was available)

### Added  
- Chain visualization as open beta feature (supports SVG, DOT, Mermaid formats)

### Removed
- Complete removal of AI release automation system and all related files
- Cleaned up project structure to focus solely on core ModuLink functionality

## [4.0.1] - 2025-06-21
### Hotfix
  Issues with the wheel from 4.0.0, this release resolves.

## [4.0.0] - 2025-06-21
### Major Migration (BREAKING CHANGES)
- Migrated all code, tests, and documentation from `modulink_next` to `modulink`.
- All import paths and references now use the new `modulink` package structure.
- Test suite and CLI updated for new structure.
- **Breaking changes:**
    - Chain architecture refactored for clarity and extensibility.
    - Removed obsolete modules and legacy code.
    - Test structure and CLI entrypoints have changed.
- Version bumped to 4.0.0 to reflect these breaking changes.

## [3.0.0] - 2025-06-21
### Major Migration
- Migrated all code, tests, and documentation from `modulink_next` to `modulink`.
- Updated all import paths and references to use the new `modulink` package structure.
- All tests passing under the new structure.
- Breaking changes: old `modulink_next` imports are no longer supported.
- Version bumped to 3.0.0 to reflect these breaking changes.


## [2.0.3] - 2025-06-10

### Added
- Major refactor with enhanced Chain architecture
- Timezone-aware timestamps (Python 3.13+ compatibility)
- Comprehensive testing infrastructure (236 tests)

## Previous Releases
- chore: remove AI release automation system, restore clean ModuLink-py project
- feat: add deprecation warning for modulink.src.context imports
- feat: enhance release.py with automation-friendly options and rollback capability
- chore: automate artifact cleanup in rollback, remove obsolete rollback_release.py
- refactor: enforce tests run first in release workflow
- fix: complete backward compatibility and update tests
- docs: add migration guide for new import patterns
- refactor: flatten package structure with backward compatibility
- ci: skip existing distributions to avoid upload conflicts
- fix: update workflow to fetch tag instead of branch
- Fix package structure for v4.0.1 - Critical import fix (#15)
- 🚨 Fix: Prevent accidental production releases from feature branches (#14)
- Update README.md
- Major migration: modulink_next → modulink, v4.0.0 release (#13)
- Update README.md
- Update README.md
- docs: update compose examples to chain
- fix: mypy python version
