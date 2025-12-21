# Changelog

Alle vesentlige endringer i dette prosjektet dokumenteres her.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)  
Versjonering: [SemVer](https://semver.org/lang/no/)

## [1.0.1] - 2025-12-21

### Changed

- Removed “direct open SOSI” mode due to stability issues and crashes.
- Plugin now focuses on converting SOSI to GeoPackage (GPKG) as the primary workflow.
- Changed icon to prepare for scaleability and bundle of plugins.

### Fixed

- The "direct open SOSI" is fixed, in the sence of it being removed.

### Notes

- The GeoPackage conversion uses fast defaults where possible and falls back to a more robust mode when required.

## [1.0.0] - 2025-12-16

### Added

- Rask åpning av SOSI direkte i QGIS.
- Konvertering til GeoPackage (rask) med progress/cancel.

### Changed

- Spatial index bygges ikke under import for bedre ytelse.

### Fixed

- Robust fallback når direkte konvertering feiler.
