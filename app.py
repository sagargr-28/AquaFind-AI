import os
from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="AquaFind AI", page_icon="💧", layout="wide")

# --------------------------- Language / styling ---------------------------
LANG = st.sidebar.selectbox("Language / ಭಾಷೆ", ["English", "ಕನ್ನಡ"])
KN = LANG == "ಕನ್ನಡ"

TEXT = {
    "title": "AquaFind AI" if not KN else "ಆಕ್ವಾಫೈಂಡ್ AI",
    "subtitle": "Groundwater prospecting assistant" if not KN else "ಭೂಗರ್ಭಜಲ ಸಂಶೋಧನಾ ಸಹಾಯಕ",
    "intro": "Compare field-survey points, review the evidence, estimate investigation costs, and export a report." if not KN else "ಸರ್ವೇ ಸ್ಥಳಗಳನ್ನು ಹೋಲಿಸಿ, ಮಾಹಿತಿಯನ್ನು ಪರಿಶೀಲಿಸಿ, ವೆಚ್ಚ ಅಂದಾಜಿಸಿ ಮತ್ತು ವರದಿ ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ.",
    "warning": "Prototype only: scores are relative screening indicators, not groundwater predictions. Resistivity can be affected by clay, salinity, rock type, and moisture. Confirm promising sites with qualified hydrogeologists and suitable field surveys." if not KN else "ಇದು ಪ್ರೋಟೋಟೈಪ್ ಮಾತ್ರ: ಸ್ಕೋರ್‌ಗಳು ಪ್ರಾಥಮಿಕ ಸೂಚಕಗಳು, ಭೂಗರ್ಭಜಲದ ಖಚಿತ ಭವಿಷ್ಯವಾಣಿ ಅಲ್ಲ. ಮಣ್ಣು, ಉಪ್ಪಿನಾಂಶ, ಬಂಡೆ ಮತ್ತು ತೇವಾಂಶವು ರೆಸಿಸ್ಟಿವಿಟಿಯನ್ನು ಬದಲಾಯಿಸಬಹುದು. ತಜ್ಞರ ಪರಿಶೀಲನೆ ಅಗತ್ಯ.",
    "data": "Survey data" if not KN else "ಸರ್ವೇ ಮಾಹಿತಿ",
    "upload": "Upload survey CSV" if not KN else "ಸರ್ವೇ CSV ಅಪ್‌ಲೋಡ್ ಮಾಡಿ",
    "sample": "Use included demonstration data" if not KN else "ಡೆಮೋ ಡೇಟಾ ಬಳಸಿ",
    "map": "Groundwater investigation map" if not KN else "ಭೂಗರ್ಭಜಲ ಪರಿಶೀಲನಾ ನಕ್ಷೆ",
    "compare": "Compare sites" if not KN else "ಸ್ಥಳಗಳನ್ನು ಹೋಲಿಸಿ",
    "analysis": "Explainable site screening" if not KN else "ಸ್ಥಳ ಪರಿಶೀಲನೆಯ ವಿವರಣೆ",
    "cost": "Investigation cost estimator" if not KN else "ಪರಿಶೀಲನಾ ವೆಚ್ಚ ಅಂದಾಜು",
    "sensor": "Add a field reading" if not KN else "ಕ್ಷೇತ್ರದ ಅಳತೆಯನ್ನು ಸೇರಿಸಿ",
    "report": "Download survey report" if not KN else "ಸರ್ವೇ ವರದಿ ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ",
    "aws": "AWS cloud integration" if not KN else "AWS ಕ್ಲೌಡ್ ಸಂಪರ್ಕ",
}
st.markdown("""
<style>
.block-container {padding-top:1.2rem; padding-bottom:2rem}
[data-testid="stMetric"] {border:1px solid #dbe4ee; padding:12px; border-radius:12px}
.small-note {color:#64748b;font-size:.88rem}
</style>
""", unsafe_allow_html=True)

st.title("💧 " + TEXT["title"])
st.subheader(TEXT["subtitle"])
st.write(TEXT["intro"])
st.warning(TEXT["warning"])

REQUIRED = ["location", "resistivity_ohm_m", "soil_moisture_pct", "rainfall_mm"]
NUMERIC = ["resistivity_ohm_m", "soil_moisture_pct", "rainfall_mm"]
SAMPLE_PATH = Path(__file__).parent / "data" / "sample_survey.csv"

@st.cache_data
def load_sample():
    return pd.read_csv(SAMPLE_PATH)

with st.sidebar:
    st.header(TEXT["data"])
    uploaded = st.file_uploader(TEXT["upload"], type=["csv"])
    use_sample = st.checkbox(TEXT["sample"], value=uploaded is None)
    st.caption("Required: " + ", ".join(REQUIRED))
    st.caption("Optional: latitude, longitude, soil_type, geology, survey_date, notes")

if "field_rows" not in st.session_state:
    st.session_state.field_rows = []

if uploaded is not None:
    try:
        raw = pd.read_csv(uploaded)
        source_label = "Uploaded CSV"
    except Exception as exc:
        st.error(f"CSV could not be read: {exc}")
        st.stop()
elif use_sample:
    raw = load_sample()
    source_label = "Simulated demonstration data"
else:
    raw = pd.DataFrame(columns=REQUIRED)
    source_label = "Manual field readings"

# Sensor / manual field input. Useful even when offline; download CSV and upload later.
with st.expander("➕ " + TEXT["sensor"], expanded=not bool(len(raw))):
    with st.form("field_reading_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        location = c1.text_input("Location / point ID", placeholder="Farm Point G")
        resistivity = c1.number_input("Electrical resistivity (Ω·m)", min_value=0.0, value=25.0, step=1.0)
        moisture = c2.number_input("Soil moisture (%)", min_value=0.0, max_value=100.0, value=30.0, step=1.0)
        rainfall = c2.number_input("Recent rainfall (mm)", min_value=0.0, value=50.0, step=5.0)
        c3, c4 = st.columns(2)
        lat = c3.number_input("Latitude (optional; 0 if unknown)", value=0.0, format="%.6f")
        lon = c4.number_input("Longitude (optional; 0 if unknown)", value=0.0, format="%.6f")
        soil_type = st.text_input("Soil / geology notes (optional)")
        add_row = st.form_submit_button("Add field reading")
    if add_row:
        if not location.strip():
            st.error("Enter a location or point ID.")
        else:
            row = {"location": location.strip(), "resistivity_ohm_m": resistivity,
                   "soil_moisture_pct": moisture, "rainfall_mm": rainfall,
                   "latitude": lat if lat != 0 else np.nan, "longitude": lon if lon != 0 else np.nan,
                   "soil_type": soil_type.strip()}
            st.session_state.field_rows.append(row)
            st.success(f"Added reading for {location}.")
    if st.session_state.field_rows:
        st.caption(f"{len(st.session_state.field_rows)} manual reading(s) queued in this session.")
        if st.button("Use manual readings with current dataset"):
            manual_df = pd.DataFrame(st.session_state.field_rows)
            if raw.empty:
                raw = manual_df
            else:
                raw = pd.concat([raw, manual_df], ignore_index=True)
            source_label += " + manual readings"

missing = set(REQUIRED) - set(raw.columns)
if missing:
    st.error("Missing required columns: " + ", ".join(sorted(missing)))
    st.stop()
if raw.empty:
    st.info("Upload a CSV, add a field reading, or enable the demonstration data.")
    st.stop()

df = raw.copy()
df["location"] = df["location"].fillna("").astype(str).str.strip()
for col in NUMERIC:
    df[col] = pd.to_numeric(df[col], errors="coerce")
df = df.dropna(subset=NUMERIC)
df = df[df["location"] != ""].copy()
if df.empty:
    st.error("No usable rows. Check that resistivity, soil moisture, and rainfall contain numeric values.")
    st.stop()
if not np.isfinite(df[NUMERIC].to_numpy(dtype=float)).all():
    st.error("Survey measurements must be finite numeric values. Check for infinity or invalid numbers.")
    st.stop()
if (df[NUMERIC] < 0).any().any():
    st.error("Resistivity, soil moisture, and rainfall values cannot be negative.")
    st.stop()
if (df["soil_moisture_pct"] > 100).any():
    st.error("Soil moisture percentages must be between 0 and 100.")
    st.stop()

def minmax(series):
    lo, hi = series.min(), series.max()
    if hi == lo:
        return pd.Series(np.full(len(series), 0.5), index=series.index)
    return (series - lo) / (hi - lo)

# Transparent heuristic, not a trained AI model or scientifically calibrated prediction.
df["resistivity_indicator"] = 1 - minmax(df["resistivity_ohm_m"].clip(lower=0))
df["moisture_indicator"] = minmax(df["soil_moisture_pct"].clip(lower=0, upper=100))
df["rainfall_indicator"] = minmax(df["rainfall_mm"].clip(lower=0))
df["screening_score"] = (0.60 * df["resistivity_indicator"] +
                         0.25 * df["moisture_indicator"] +
                         0.15 * df["rainfall_indicator"]) * 100
df["screening_band"] = pd.cut(df["screening_score"], [-1, 35, 65, 101],
                              labels=["Lower screening priority", "Moderate screening priority", "Higher screening priority"])

def explain(row):
    reasons = []
    # Relative comparisons only, within the currently loaded dataset.
    if row["resistivity_indicator"] >= 0.67:
        reasons.append("relatively lower resistivity in this dataset")
    elif row["resistivity_indicator"] <= 0.33:
        reasons.append("relatively higher resistivity in this dataset")
    if row["moisture_indicator"] >= 0.67:
        reasons.append("relatively higher soil moisture")
    elif row["moisture_indicator"] <= 0.33:
        reasons.append("relatively lower soil moisture")
    if row["rainfall_indicator"] >= 0.67:
        reasons.append("relatively higher rainfall")
    elif row["rainfall_indicator"] <= 0.33:
        reasons.append("relatively lower rainfall")
    return "; ".join(reasons) if reasons else "measurements are near the dataset's middle range"

df["reasoning"] = df.apply(explain, axis=1)
df["data_quality"] = "Basic"
if {"latitude", "longitude"}.issubset(df.columns):
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    valid_coords = df["latitude"].between(-90, 90) & df["longitude"].between(-180, 180)
    df.loc[valid_coords, "data_quality"] = "Coordinates available"

top = df.sort_values("screening_score", ascending=False).iloc[0]
m1, m2, m3, m4 = st.columns(4)
m1.metric("Survey points", len(df))
m2.metric("Top screening score", f"{top['screening_score']:.0f}/100")
m3.metric("Mean resistivity", f"{df['resistivity_ohm_m'].mean():.1f} Ω·m")
m4.metric("Data source", "Sample" if "Simulated" in source_label else ("Uploaded / field" if "Uploaded" in source_label or "manual" in source_label.lower() else "Field"))
st.caption(f"Source: {source_label}. Scores are relative to the current dataset; adding/removing rows can change rankings.")

tabs = st.tabs([TEXT["map"], TEXT["compare"], TEXT["analysis"], TEXT["cost"], TEXT["report"], TEXT["aws"]])

# 1) Map
with tabs[0]:
    st.markdown("### " + TEXT["map"])
    if {"latitude", "longitude"}.issubset(df.columns):
        coords = df.copy()
        coords = coords.dropna(subset=["latitude", "longitude"])
        coords = coords[coords["latitude"].between(-90, 90) & coords["longitude"].between(-180, 180)]
        # Zero coordinates often mean "unknown" in manual entry; don't plot them.
        coords = coords[~((coords["latitude"] == 0) & (coords["longitude"] == 0))]
        if not coords.empty:
            figmap = px.scatter_map(coords, lat="latitude", lon="longitude", color="screening_band",
                                       size="screening_score", hover_name="location",
                                       hover_data=["resistivity_ohm_m", "soil_moisture_pct", "rainfall_mm", "screening_score"],
                                       zoom=10, height=480,
                                       map_style="open-street-map",
                                       color_discrete_map={"Higher screening priority":"#16a34a",
                                                           "Moderate screening priority":"#eab308",
                                                           "Lower screening priority":"#dc2626"},
                                       labels={"screening_score":"Screening score", "screening_band":"Relative band"})
            st.plotly_chart(figmap, use_container_width=True)
        else:
            st.info("No valid coordinates available. Add latitude/longitude to the CSV or field form to display map markers.")
    else:
        st.info("Add latitude and longitude columns to show survey locations on the map.")
    st.caption("Map colors indicate relative screening priority only, not confirmed groundwater.")

# 2) Site comparison
with tabs[1]:
    st.markdown("### " + TEXT["compare"])
    ranked = df.sort_values("screening_score", ascending=False)
    selected = st.multiselect("Choose locations to compare", ranked["location"].tolist(),
                              default=ranked["location"].head(min(3, len(ranked))).tolist())
    comp = ranked[ranked["location"].isin(selected)]
    if not comp.empty:
        fig = px.bar(comp, x="location", y="screening_score", color="screening_band",
                     hover_data=["resistivity_ohm_m", "soil_moisture_pct", "rainfall_mm"],
                     labels={"location":"Survey point", "screening_score":"Relative screening score"})
        fig.update_layout(yaxis_range=[0, 100], xaxis_tickangle=-20)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(comp[["location", "resistivity_ohm_m", "soil_moisture_pct", "rainfall_mm", "screening_score", "screening_band"]].round(2),
                     use_container_width=True, hide_index=True)
    else:
        st.info("Select at least one location to compare.")

# 3) Explainable analysis + charts
with tabs[2]:
    st.markdown("### " + TEXT["analysis"])
    left, right = st.columns(2)
    with left:
        fig = px.bar(df.sort_values("screening_score", ascending=False), x="location", y="screening_score",
                     color="screening_band", labels={"screening_score":"Relative screening score", "location":"Location"})
        fig.update_layout(yaxis_range=[0, 100], xaxis_tickangle=-25)
        st.plotly_chart(fig, use_container_width=True)
    with right:
        fig2 = px.scatter(df, x="resistivity_ohm_m", y="soil_moisture_pct", size="rainfall_mm",
                          color="screening_band", hover_name="location",
                          labels={"resistivity_ohm_m":"Resistivity (Ω·m)", "soil_moisture_pct":"Soil moisture (%)"})
        st.plotly_chart(fig2, use_container_width=True)
    st.markdown("#### Why each site received its relative score")
    st.dataframe(df[["location", "screening_score", "screening_band", "reasoning"]].sort_values("screening_score", ascending=False).round(2),
                 use_container_width=True, hide_index=True)
    st.info("This is an explainable rule-based screening heuristic, not a trained AI model. Resistivity alone cannot establish water presence; clay and salinity can also produce low readings.")

# 4) Cost estimator
with tabs[3]:
    st.markdown("### " + TEXT["cost"])
    c1, c2, c3 = st.columns(3)
    drilling_cost = c1.number_input("Estimated drilling cost per attempt (₹)", min_value=0, value=80000, step=5000)
    survey_cost = c2.number_input("Professional survey cost per site (₹)", min_value=0, value=5000, step=500)
    sites_to_survey = c3.number_input("Sites to survey first", min_value=1, max_value=100, value=min(3, len(df)), step=1)
    attempts = st.slider("Possible drilling attempts without survey", min_value=1, max_value=10, value=2)
    survey_total = int(survey_cost * sites_to_survey)
    baseline = int(drilling_cost * attempts)
    potential_difference = baseline - survey_total
    a, b, c = st.columns(3)
    a.metric("Survey budget", f"₹{survey_total:,.0f}")
    b.metric("Illustrative drilling spend", f"₹{baseline:,.0f}")
    c.metric("Difference before other costs", f"₹{potential_difference:,.0f}", delta=None)
    st.caption("Illustrative arithmetic only. This is not a savings guarantee. Actual costs depend on geology, depth, contractor, location, and whether a well succeeds.")
    st.markdown("#### Suggested order for further investigation")
    st.dataframe(df.sort_values("screening_score", ascending=False)[["location", "screening_band", "reasoning"]].head(int(sites_to_survey)),
                 use_container_width=True, hide_index=True)

# 5) Report and CSV export
with tabs[4]:
    st.markdown("### " + TEXT["report"])
    st.write("Export the analyzed rows for a field team or attach them to a project submission.")
    export_df = df.copy().sort_values("screening_score", ascending=False)
    st.download_button("Download analyzed CSV", data=export_df.to_csv(index=False).encode("utf-8"),
                       file_name="aquafind_analyzed_survey.csv", mime="text/csv")
    report_lines = [
        "# AquaFind AI - Preliminary Survey Report", "",
        f"Data source: {source_label}", f"Survey points analyzed: {len(df)}", "",
        "## Highest relative screening score", f"- Location: {top['location']}",
        f"- Relative screening score: {top['screening_score']:.1f}/100",
        f"- Screening band: {top['screening_band']}", f"- Explanation: {top['reasoning']}", "",
        "## Ranked locations"
    ]
    for _, row in export_df.iterrows():
        report_lines.append(f"- {row['location']}: {row['screening_score']:.1f}/100 ({row['screening_band']}); {row['reasoning']}")
    report_lines += ["", "## Limitations",
        "Scores are relative, illustrative indicators calculated from the current dataset, not groundwater predictions.",
        "Resistivity is affected by geology, clay, salinity, moisture, and survey method. A qualified professional should validate any proposed borewell location."]
    report_text = "\n".join(report_lines)
    st.download_button("Download text survey report", data=report_text.encode("utf-8"),
                       file_name="aquafind_survey_report.md", mime="text/markdown")
    st.caption("PDF export can be added with a PDF library; Markdown and CSV exports work without extra dependencies.")

# 6) AWS cloud integration: optional, never required for local demo
with tabs[5]:
    st.markdown("### " + TEXT["aws"])
    st.write("Cloud integration is optional. The dashboard remains usable locally without AWS credentials.")
    st.markdown("""
    - **Amazon S3:** archive survey CSVs.
    - **Amazon DynamoDB:** store survey-point metadata and results.
    - **AWS Lambda:** run a server-side processing workflow through a secured function URL or API Gateway.
    - **AWS IoT Core:** connect sensor hardware through an authenticated MQTT device/client workflow.
    """)
    st.warning("Never paste AWS access keys into this app or commit them to GitHub. Configure credentials through the AWS CLI/instance role and grant least-privilege permissions.")
    s3_bucket = st.text_input("Optional S3 bucket name", value=os.getenv("AQUAFIND_S3_BUCKET", ""))
    aws_region = st.text_input("AWS region", value=os.getenv("AWS_DEFAULT_REGION", "ap-south-1"))
    if st.button("Upload analyzed CSV to S3"):
        if not s3_bucket.strip():
            st.error("Enter an S3 bucket name first.")
        else:
            try:
                import boto3
                from botocore.exceptions import BotoCoreError, ClientError
                from datetime import datetime, timezone
                key = f"aquafind/surveys/survey-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.csv"
                client = boto3.client("s3", region_name=aws_region.strip() or None)
                client.put_object(Bucket=s3_bucket.strip(), Key=key, Body=export_df.to_csv(index=False).encode("utf-8"),
                                  ContentType="text/csv")
                st.success(f"Uploaded to s3://{s3_bucket.strip()}/{key}")
            except ImportError:
                st.error("Optional AWS SDK missing. Install boto3, then restart the app.")
            except Exception as exc:
                st.error(f"S3 upload failed. Check AWS credentials, bucket policy, and region. Details: {exc}")
    st.caption("S3 upload requires boto3, valid AWS credentials, and permission to s3:PutObject. DynamoDB, Lambda, and IoT Core are documented integration paths, not enabled automatically.")

st.markdown("---")
st.markdown("<p class='small-note'>AquaFind AI • Hackathon prototype • Preliminary screening support only. Not a substitute for a professional groundwater survey.</p>", unsafe_allow_html=True)
