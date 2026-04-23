# Roadmap

## Current Focus

- Ship a stable Cura plugin with manual import from Spoolman
- Keep the integration read-only
- Improve connection and import workflow inside Cura

## Implemented or In Progress

- Configurable Spoolman base URL
- Connection test action inside Cura
- Import preview action before writing materials
- Best-effort live material reload after import with restart fallback messaging
- GitHub packaging workflow and versioned plugin zip artifacts

## Next

- Runtime validation of live reload behavior across Cura versions
- Screenshots or a short demo for the repository page

## Future

### Conflict Handling

- Detect possible naming or metadata conflicts before import
- Warn when multiple Spoolman filaments map to confusingly similar Cura materials
- Add safer overwrite behavior for manually modified generated materials

### Better Metadata Support

- Richer XML mapping for temperature ranges, notes, color families, and supplier identifiers
- Material-specific templates for PLA, PETG, ABS, TPU, and similar families
- Better handling for article numbers and external supplier references
- Validation and warnings for unusual or missing diameter values

### Material Naming and Filtering

- User-selectable naming formats for imported materials
- Filter by material type, vendor, archived state, or active spool state
- Selective import instead of importing every eligible filament definition
