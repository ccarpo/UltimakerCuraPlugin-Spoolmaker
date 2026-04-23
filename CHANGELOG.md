# Changelog

All notable changes to this project should be documented in this file.

## 0.2.0

Configuration and workflow improvements.

### Added

- MIT license for the repository
- Configurable Spoolman base URL stored in Cura preferences
- Connection test action inside the Cura plugin
- Import preview action with spool and filament summary counts
- Best-effort live material reload attempt after import
- Repository roadmap document for planned and future features
- Local packaging script for building a versioned Cura plugin zip
- GitHub Actions workflow for packaging and tagged releases
- Release instructions document for publishing artifacts

### Notes

- Live reload remains best-effort and may still require a Cura restart, especially for updates to existing materials.

## 0.1.0

Initial implementation.

### Added

- Cura extension plugin scaffold
- Manual menu action to import materials from Spoolman
- HTTP client for reading spools from the Spoolman API
- Deduplication by `filament.id`
- Cura material XML generation for imported filaments
- Stable generated filenames and GUIDs for repeatable imports
- Import result summary shown inside Cura
- Basic repository documentation for installation and contribution

### Notes

- The integration is read-only.
- The Spoolman base URL is currently fixed in code.
- Cura may require a restart before newly generated materials appear.
