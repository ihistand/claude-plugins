# Error ledger

### E-001 Empty import file crashed the importer
Detected: 2026-10-29, test failure in T-001.3
Classification: code bug
Diagnosis: the importer indexed the first row of an empty file; AC-001.3 was right
Resolution: the importer returns status `empty` before reading rows; T-001.3 passes
Recurrence of: -
