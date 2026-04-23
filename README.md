# Spoolman Materials for Cura

Import filament definitions from [Spoolman](https://github.com/Donkie/Spoolman) into UltiMaker Cura as material profiles.

## Overview

This plugin adds a manual import action to Cura that reads spools from a Spoolman instance, groups them by `filament.id`, and generates Cura `.xml.fdm_material` files.

The current version is intentionally read-only:

- It reads spool and filament data from Spoolman.
- It creates or updates generated Cura materials.
- It does not write spool usage, assignments, or inventory changes back to Spoolman.

## Current Features

- Configurable Spoolman base URL stored in Cura preferences
- Connection test action inside Cura
- Import preview action inside Cura
- Manual import action inside Cura
- One Cura material per Spoolman filament definition
- Stable filenames and GUIDs so repeated imports update existing generated materials
- Mapping of common filament metadata into Cura material XML
- Graceful skipping of malformed or incomplete records
- Best-effort live reload after import with restart fallback messaging
- Summary message after each import

## Requirements

- UltiMaker Cura with plugin support
- A reachable Spoolman instance
- Python runtime bundled with Cura

## Configuring the Spoolman URL

Use the Cura menu to configure the Spoolman server URL:

- `Spoolman -> Configure Spoolman URL`
- `Spoolman -> Test Spoolman connection`

The configured URL is stored in Cura preferences and reused on the next start.

If no saved value exists yet, the plugin falls back to the default defined in `SpoolmanClient.py`.

## Installation

### Windows

Copy this repository folder into Cura's plugins directory for your installed Cura version:

```text
%APPDATA%\cura\<version>\plugins\UltimakerCuraPlugin-Spoolmaker
```

Example:

```text
C:\Users\<YourUser>\AppData\Roaming\cura\5.9\plugins\UltimakerCuraPlugin-Spoolmaker
```

After copying the files, restart Cura.

## Usage

1. Start Spoolman.
2. Open Cura.
3. Optionally use `Spoolman -> Configure Spoolman URL`.
4. Optionally use `Spoolman -> Test Spoolman connection`.
5. Optionally use `Spoolman -> Preview import from Spoolman`.
6. Use `Spoolman -> Import materials from Spoolman`.
7. Review the result message shown by the plugin.
8. If the new materials do not appear immediately, restart Cura.

## Data Mapping

The plugin currently attempts to map these Spoolman filament fields into Cura material profiles when available:

- Vendor or brand
- Filament name
- Material type
- Color information
- Diameter
- Density
- Weight
- Extruder temperature
- Bed temperature
- Comment and external identifiers

## Generated Files

Generated material profiles are written into Cura's writable data directory under a `spoolman` subfolder.

The plugin only removes stale files that it previously generated in that managed subfolder.

## Repository Structure

```text
plugin.json
__init__.py
SpoolmanClient.py
SpoolmanMaterialExtension.py
MaterialWriter.py
package_plugin.py
LICENSE
README.md
CONTRIBUTING.md
CHANGELOG.md
ROADMAP.md
RELEASING.md
.github/workflows/package-plugin.yml
```

## Development

A quick local syntax check:

```bash
python -c 'from pathlib import Path; files=[r"f:\Code\Private\UltimakerCuraPlugin-Spoolmaker\__init__.py", r"f:\Code\Private\UltimakerCuraPlugin-Spoolmaker\SpoolmanClient.py", r"f:\Code\Private\UltimakerCuraPlugin-Spoolmaker\MaterialWriter.py", r"f:\Code\Private\UltimakerCuraPlugin-Spoolmaker\SpoolmanMaterialExtension.py"]; [compile(Path(file).read_text(encoding="utf-8"), file, "exec") for file in files]; print("syntax-ok")'
```

See `CONTRIBUTING.md` for a lightweight workflow.

## Known Limitations

- Live material reload is only a best-effort attempt and may not fully refresh updated existing materials without a restart.
- The plugin currently focuses on importing materials, not selecting active spools.
- The XML generation is intentionally conservative and does not yet provide advanced per-material print tuning.

## Publishing Checklist

Before publishing on GitHub, consider adding:

- Screenshots or a short demo GIF
- Example Spoolman payloads or test fixtures
- Optional automation guidance such as `AGENTS.md` or `llms.txt` if you want to steer bots or AI agents

## Packaging and Releases

This repository now includes automated packaging for GitHub and a reusable local packaging script.

- Local packaging script: `package_plugin.py`
- GitHub Actions workflow: `.github/workflows/package-plugin.yml`
- Release instructions: `RELEASING.md`

The generated zip contains the plugin in a top-level `UltimakerCuraPlugin-Spoolmaker` folder so it can be extracted directly into Cura's plugins directory.

## Roadmap

See `ROADMAP.md` for current priorities and future items including conflict handling, richer metadata support, and material naming or filtering improvements.

## Status

The plugin now supports configurable connection settings, connection testing, preview before import, best-effort live reload, and GitHub packaging automation. Runtime verification inside a live Cura instance remains the main next validation step.
