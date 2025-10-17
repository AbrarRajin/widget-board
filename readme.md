## Development Status

**Current Milestone**: M3 - Plugin Runtime (In-Process Prototype) ✓

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

### M3 - Plugin Runtime (In-Process Prototype) ✓
- [x] Plugin base class and lifecycle (INIT → START → UPDATE → DISPOSE)
- [x] Plugin manifest parser (manifest.json)
- [x] Plugin loader and registry
- [x] Dynamic plugin discovery
- [x] Example plugins (Clock, Quick Links)
- [x] Plugin rendering in tiles
- [x] Plugin menu with discovered plugins
- [x] Per-instance plugin settings

### Next: M4 - Out-of-Process Plugin Isolation
M4 updated in 17th Friday check