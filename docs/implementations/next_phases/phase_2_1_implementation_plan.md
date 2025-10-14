# Phase 2: Remaining High-Impact Features

## Overview

Implement 4 critical features to complete Phase 2 GUI enhancements: full-featured results export, comprehensive validation system, settings persistence, and enhanced error handling.

## 1. Full-Featured Results Export (Priority 3.5)

### 1.1 Enhance Results Panel Export Menu

**File**: `src/backtester/gui/widgets/results_panel.py` (lines 380-450)

Current implementation has basic export stubs. Enhance to:

- Implement actual PDF export with charts and formatted tables
- Implement Excel export with multiple sheets (Summary, Trades, Equity)
- Add formatting and styling to exports
- Include embedded charts in PDF/Excel
- Add export progress indicator for large datasets

**Dependencies**:

- `reportlab` for PDF generation
- `openpyxl` for Excel with charts
- `matplotlib` for chart generation

### 1.2 Create Export Utility Module

**New File**: `src/backtester/gui/utils/export_manager.py`

Create reusable export utilities:

- `PDFExporter` class with chart embedding
- `ExcelExporter` class with multi-sheet support
- `CSVExporter` class with proper encoding
- `JSONExporter` class with serialization handling
- Common formatting utilities for all exporters

### 1.3 Add Export Configuration Dialog

**New File**: `src/backtester/gui/dialogs/export_dialog.py`

Create export options dialog:

- Format selection (PDF, Excel, CSV, JSON)
- Content selection (which tabs to include)
- Chart options (resolution, size, colors)
- File naming templates
- Export preview before saving

## 2. Comprehensive Validation System (Priority 2.6)

### 2.1 Create Validation Framework

**New File**: `src/backtester/gui/utils/validation_engine.py`

Build validation system with:

- `ValidationRule` base class
- `ValidationResult` with severity levels (ERROR, WARNING, INFO)
- `ValidationEngine` to run all rules
- Built-in rules for common validations
- Auto-fix suggestion framework

### 2.2 Enhance Strategy Builder Validation Panel

**File**: `src/backtester/gui/widgets/strategy_builder.py` (lines 294-375)

Transform basic validation panel:

- Real-time validation as user modifies strategy
- Expandable tree view for validation results
- Severity icons (red X, yellow warning, blue info)
- "Quick Fix" buttons for auto-fixable issues
- Validation rule documentation tooltips
- Filter by severity level

### 2.3 Add Backtest Configuration Validation

**File**: `src/backtester/gui/widgets/backtest_config.py`

Add real-time parameter validation:

- Visual feedback on input fields (red border for errors)
- Inline validation messages below fields
- Range validation with suggested values
- Dependency validation (e.g., stop_loss < take_profit)
- Warning indicators for extreme values
- "Fix All" button for batch corrections

### 2.4 Create Validation Rules Library

**New File**: `src/backtester/gui/utils/validation_rules.py`

Implement specific validation rules:

- `NoSignalsRule`: Warn if strategy has no signals
- `DuplicateSignalRule`: Warn about duplicate signals
- `ParameterRangeRule`: Validate parameter ranges
- `SignalConflictRule`: Detect conflicting signals
- `ConfigurationConsistencyRule`: Check config consistency
- Each rule with auto-fix suggestion

## 3. Settings System with Persistence (Priority 5.1)

### 3.1 Create Settings Manager

**New File**: `src/backtester/gui/settings_manager.py`

Implement simple key-value settings system:

- `SettingsManager` singleton class
- Load/save to JSON file (`~/.backtester/settings.json`)
- Default values for all settings
- Type-safe get/set methods
- Settings categories (ui, data, execution, export)
- Auto-save on change

### 3.2 Define Settings Schema

**New File**: `src/backtester/gui/data/default_settings.json`

Create default settings structure:

```json
{
  "ui": {
    "window_geometry": null,
    "splitter_states": {},
    "last_tab": 0,
    "show_tooltips": true
  },
  "data": {
    "last_data_path": "",
    "recent_files": [],
    "auto_cache": true
  },
  "execution": {
    "auto_open_results": true,
    "show_progress_details": true
  },
  "export": {
    "default_format": "pdf",
    "include_charts": true,
    "default_path": ""
  }
}
```

### 3.3 Integrate Settings into Main Window

**File**: `src/backtester/gui/main_window.py`

Add settings integration:

- Load window geometry on startup
- Save window geometry on close
- Restore last active tab
- Save/restore splitter positions
- Add "Preferences" menu item (basic dialog for now)

### 3.4 Create Basic Settings Dialog

**New File**: `src/backtester/gui/dialogs/settings_dialog.py`

Simple settings dialog with:

- General tab (tooltips, auto-open results)
- Data tab (cache settings, recent files limit)
- Export tab (default format, include charts)
- "Reset to Defaults" button
- "Apply" and "OK" buttons

## 4. Enhanced Error Handling (Priority 1.4)

### 4.1 Create Error Handler Utility

**New File**: `src/backtester/gui/utils/error_handler.py`

Build centralized error handling:

- `ErrorHandler` class with logging
- User-friendly error message mapping
- Error severity classification
- Actionable error suggestions
- Error reporting dialog with details
- Copy error details to clipboard

### 4.2 Create Custom Error Dialogs

**New File**: `src/backtester/gui/dialogs/error_dialog.py`

Professional error dialogs:

- `ErrorDialog` with icon, title, message
- Expandable "Technical Details" section
- Suggested actions list
- "Report Bug" button (copies to clipboard)
- "Ignore" vs "Retry" vs "Cancel" options
- Toast notifications for minor errors

### 4.3 Update Controllers with Error Handling

**Files**:

- `src/backtester/gui/controllers/execution_controller.py`
- `src/backtester/gui/controllers/strategy_controller.py`

Wrap operations with error handling:

- Try-catch blocks with user-friendly messages
- Log technical details to file
- Show actionable error dialogs
- Graceful degradation for non-critical errors
- Progress cancellation on errors

### 4.4 Add Error Messages Mapping

**New File**: `src/backtester/gui/data/error_messages.json`

Map technical errors to user messages:

```json
{
  "FileNotFoundError": {
    "title": "File Not Found",
    "message": "The selected file could not be found.",
    "suggestions": [
      "Check if the file path is correct",
      "Ensure the file hasn't been moved or deleted",
      "Try selecting the file again"
    ]
  },
  "ValueError": {
    "title": "Invalid Value",
    "message": "One or more parameters have invalid values.",
    "suggestions": [
      "Check parameter ranges in tooltips",
      "Ensure all required fields are filled",
      "Review validation warnings"
    ]
  }
}
```

## Implementation Order

1. **Settings System** (Foundation)

   - Implement SettingsManager and persistence
   - Integrate into main window
   - Create basic settings dialog

2. **Error Handling** (Infrastructure)

   - Create ErrorHandler utility
   - Build custom error dialogs
   - Update controllers with error handling

3. **Validation System** (Core Feature)

   - Build validation framework
   - Implement validation rules
   - Enhance strategy builder validation panel
   - Add backtest config validation

4. **Results Export** (Polish)

   - Install dependencies (reportlab, openpyxl)
   - Create export manager utility
   - Implement PDF/Excel/CSV/JSON exporters
   - Add export configuration dialog

## Testing Checklist

- [ ] Settings persist across application restarts
- [ ] Window geometry and splitter positions restore correctly
- [ ] Error dialogs show user-friendly messages
- [ ] Technical error details are logged to file
- [ ] Validation runs in real-time without lag
- [ ] Auto-fix suggestions work correctly
- [ ] PDF export includes formatted tables and charts
- [ ] Excel export has multiple sheets with proper formatting
- [ ] CSV export handles special characters correctly
- [ ] JSON export is valid and complete
- [ ] Export progress indicator shows for large datasets
- [ ] All exports can be opened in respective applications

## Success Criteria

- Settings system saves/loads reliably with no data loss
- Error messages are clear and actionable for non-technical users
- Validation catches common mistakes before backtest execution
- Exports produce professional-looking reports suitable for sharing
- No performance degradation from real-time validation
- All features integrate seamlessly with existing UI
