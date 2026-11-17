# Validation tests

Run `python -B -m unittest discover -s tests -v` for offline comparison, workbook parsing, and mocked HTTP tests. Fixtures are invented and contain no original invoice artifacts. Tests never call Azure. Temporary workbook fixtures stay under ignored `private/test-temp/`.

Duplicate and line-item validation remain future work. Live extraction is a separate, explicitly invoked experiment; an offline pass is not evidence of Azure access.
