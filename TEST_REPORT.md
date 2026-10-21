# AquaFind AI - Test Report

**Test date:** 21 October 2026  
**Result:** 13/13 automated smoke scenarios passed.

## Scenarios exercised

1. Default sample-data dashboard, including all six tabs, four Plotly charts, three data tables, and both downloadable exports.
2. CSV upload with valid survey rows and coordinates.
3. Missing required CSV columns produce a visible validation error.
4. Negative survey measurements are rejected.
5. Soil moisture above 100% is rejected.
6. Infinite numeric values are rejected.
7. Blank location rows are excluded rather than becoming the string `nan`.
8. Manual field-reading submission and dashboard scoring.
9. Successful S3 upload code path with a mocked S3 client.
10. Map's no-coordinate fallback message.
11. A single-site dataset with constant measurements receives a finite score.
12. Kannada interface labels render through the app's language selection.
13. S3 failure code path shows a user-facing error, using a mocked failure.

## Scope and limitations

These are automated smoke tests that execute the app using a controlled Streamlit API stub. They verify the app's Python execution paths, chart construction, data processing, and export payloads; they are **not** a live browser test of Streamlit. A live launch was not possible in the test environment because Streamlit is not installed and package installation could not reach the package index. Real AWS credentials, an actual S3 bucket, browser map tiles, and sensor hardware were not tested.

AquaFind AI's score is a relative rule-based screening heuristic, not a trained model or validated groundwater prediction. The sample survey data is simulated. Do not use these scores alone to decide where to drill.
