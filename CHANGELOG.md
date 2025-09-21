# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2025-09-21
### Added
- Discord slash commands for ping, amidakuji execution, template creation, management, and sharing.
- Flow controller architecture with dedicated handlers, actions, and views for each amidakuji state.
- Firebase-backed data manager that persists templates, member assignments, and history snapshots.
- Result embed generator supporting compact and detailed layouts plus selection mode toggles.
- Test suite covering flow controllers, database manager behaviors, data processors, and UI views (56 tests passing).

### Changed
- Hardened configuration loading with explicit validation and logging for missing environment variables.
- Docker build now installs dependencies via Poetry in system mode for lean runtime images.

### Documentation
- Expanded README with setup instructions, test guidance, and documentation map to prepare for the v0.1.0 release.
