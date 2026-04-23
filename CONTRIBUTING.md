# Contributing

Thanks for considering improvements to the plugin.

## Scope

This repository contains a Cura extension plugin that imports Spoolman filament definitions as Cura material profiles.

Please keep changes aligned with the current project goals:

- Read from Spoolman
- Import or update Cura materials on demand
- Keep the integration read-only unless the project direction explicitly changes

## Development Notes

- Keep imports at the top of each file.
- Prefer small, targeted changes.
- Avoid changing generated material behavior unless you also explain migration or compatibility impact.
- Preserve stable material identifiers when possible so repeated imports do not create duplicates.

## Manual Testing

Before opening a pull request, test at least the following:

1. Cura loads the plugin without errors.
2. The menu action appears under `Spoolman`.
3. Import succeeds against a reachable Spoolman instance.
4. Re-running import updates existing generated materials instead of duplicating them.
5. Malformed spool or filament records are skipped gracefully.

## Pull Requests

Please include:

- A short description of the change
- Why the change is needed
- Manual test notes
- Screenshots if the Cura UI changes

## Feature Requests

Good candidates for future work include:

- Configurable Spoolman connection settings
- Better material profile mapping
- Live reload of generated materials
- Filtering and preview UX inside Cura
