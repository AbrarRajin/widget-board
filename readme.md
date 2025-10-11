# WidgetBoard

A grid-based dashboard application for desktop with plugin-based widgets.

## Architecture

- **UI**: PySide6 (Qt 6)
- **IPC**: ZeroMQ for out-of-process plugins
- **Storage**: SQLite
- **Python**: 3.11+

## Installation

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Running

```bash
python -m app.main
```

## Project Structure

- `app/` - Entry points and bootstrap
- `core/` - Core models, services, config
- `ui/` - PySide6 views and widgets
- `plugins_host/` - Plugin supervisor and IPC
- `ipc/` - Message schemas
- `schema/` - JSON Schema files
- `storage/` - SQLite repository and migrations
- `themes/` - Theme token JSON files
- `examples/` - Example plugins
- `tests/` - Test suite
- `packaging/` - PyInstaller specs
- `tools/` - Development scripts

## Development Status

**Current Milestone**: M2 - Settings & Schema Rendering ✓

### M0 - Skeleton & Bootstrapping ✓
- [x] Basic PySide6 window
- [x] Theme manager (light/dark)
- [x] SQLite storage layer
- [x] Configuration system
- [x] Logging setup

### M1 - Grid MVP ✓
- [x] 8×8 grid system with visual overlay
- [x] Edit mode toggle (Ctrl+E)
- [x] Drag & drop tiles
- [x] Resize tiles (drag handle or Shift+arrows)
- [x] Collision detection (deterministic)
- [x] Layout persistence to SQLite
- [x] Keyboard accessibility (arrow keys)
- [x] Page management (create, delete, navigate)
- [x] Snap-to-grid behavior

### M2 - Settings & Schema Rendering ✓
- [x] JSON Schema loader and validator
- [x] Settings form builder (auto-generates Qt forms)
- [x] Per-instance widget settings
- [x] Global app settings panel
- [x] Import/export layouts as JSON
- [x] Schema validation
- [x] Settings dialog with Restore Defaults
- [x] Context menu on tiles (right-click)

### Next: M3 - Plugin Runtime (In-Process Prototype)

## Features

### Current (M2)
- **Grid Layout**: 8×8 cell-based grid with snap-to-grid
- **Edit Mode**: Toggle with Ctrl+E to rearrange dashboard
- **Drag & Drop**: Move tiles by dragging
- **Resize**: Drag bottom-right corner or use Shift+arrows
- **Multi-Page**: Create multiple dashboard pages
- **Settings System**:
  - JSON Schema-based settings
  - Auto-generated forms
  - Per-widget configuration
  - Global app preferences
- **Import/Export**:
  - Save layouts to JSON
  - Load layouts from JSON
  - Merge or replace modes
  - Validation before import
- **Context Menu**: Right-click tiles for options
- **Auto-Save**: Layout automatically saved to database
- **Keyboard Control**:
  - Arrow keys: Move selected tile
  - Shift+Arrows: Resize tile
  - Delete: Remove tile
  - Ctrl+E: Toggle edit mode
  - Ctrl+T: Add test tile

### Coming Soon
- M3: Plugin system (in-process prototype)
- M4: Out-of-process plugin isolation
- M5: Data-first rendering with tile chrome
- M8: Plugin manager and examples

## License

Checking if Git push works 2:06 AM