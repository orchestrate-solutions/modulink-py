# Changelog

## [4.0.3] - 2025-06-27
### Removed
- Complete removal of AI release automation system and all related files
- Cleaned up project structure to focus solely on core ModuLink functionality

### Changed
- Restored clean project structure with only core ModuLink components
- Separated AI automation project into independent repository

## Previous Changes
## v4.0.2
- chore: remove AI release automation system, restore clean ModuLink-py project focus
- fix: correct mypy python_version configuration in pyproject.toml

## Previous Releases
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
