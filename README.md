# AquaFind AI

Streamlit prototype for preliminary groundwater survey workflows.

## Features
1. Interactive map with coordinate-based survey points and relative screening bands.
2. CSV import and manual field-reading entry.
3. Explainable rule-based screening score and measurement charts.
4. Editable drilling-versus-survey cost estimator.
5. Downloadable analyzed CSV and Markdown report.
6. Optional Amazon S3 upload. AWS DynamoDB, Lambda, and IoT Core are documented extension points requiring separate configuration.
Also includes English/Kannada labels and data/accuracy caveats.

## Run locally
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## CSV schema
Required: `location`, `resistivity_ohm_m`, `soil_moisture_pct`, `rainfall_mm`
Optional: `latitude`, `longitude`, `soil_type`, `geology`, `survey_date`, `notes`.
See `data/sample_survey.csv`.

## Optional S3 upload
Install `boto3`, configure credentials using AWS CLI or an IAM role, create an S3 bucket, and grant least-privilege `s3:PutObject` permission for the target bucket/prefix. Enter bucket and region in the AWS tab. Never hardcode AWS keys or commit them to GitHub.

## Screening-score limitation
The score is an illustrative relative heuristic calculated from the currently loaded dataset: 60% inverse min-max normalized resistivity, 25% normalized soil moisture, and 15% normalized rainfall. It is not a trained AI model or validated groundwater prediction. Rankings change as the dataset changes. Clay, salinity, rock type, and moisture can affect resistivity. Use professional geophysical interpretation and verified well outcomes before making drilling decisions. Sample readings are simulated.

## Testing
See [TEST_REPORT.md](TEST_REPORT.md) for the automated smoke-test results and limits. A real browser run, connected AWS bucket, and field sensor integration still need environment-specific validation.
